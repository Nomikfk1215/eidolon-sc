"""Imported media belongs to the recorded turn and remains private to its user."""

import base64
import json
from dataclasses import replace

from eidolon.affinity_judge import OUT_OF_LINE, QUESTIONS, questions_for
from eidolon.config import LLMSettings, Settings
from eidolon.llm import LLMError
from tests.conftest import ClientFactory
from tests.fakes import FakeLLM
from tests.test_text_turn import start_conversation


async def test_picture_only_turn_keeps_its_image_and_checks_ownership(make_client: ClientFactory):
    image = b"a test picture"
    data_url = "data:image/png;base64," + base64.b64encode(image).decode()
    llm = FakeLLM(["一幅风景\n不确定"], ["<ja>いいですね</ja><zh>真好看</zh>"])
    client = make_client(llm)
    conversation = await start_conversation(client)
    response = await client.post(
        f"/api/conversations/{conversation}/turns", json={"text": "", "image": data_url}
    )
    events = [json.loads(line[6:]) for line in response.text.splitlines() if line.startswith("data: ")]
    assert events[-1]["type"] == "done", events
    entries = (await client.get(f"/api/conversations/{conversation}/messages")).json()
    message = next(entry for entry in entries if entry.get("role") == "user")
    assert message["image"] is True
    path = f"/api/messages/{message['id']}/image"
    picture = await client.get(path)
    assert picture.status_code == 200
    assert picture.content == image
    assert picture.headers["content-type"] == "image/png"
    stranger = make_client(FakeLLM(), user="someone-else")
    assert (await stranger.get(path)).status_code == 404


async def test_a_failed_picture_turn_does_not_attach_to_an_older_message(make_client: ClientFactory):
    llm = FakeLLM(
        ["<ja>はい</ja><zh>好的</zh>"], ["一幅风景\n不确定"], LLMError("unavailable")
    )
    client = make_client(llm)
    conversation = await start_conversation(client)
    path = f"/api/conversations/{conversation}/turns"
    await client.post(path, json={"text": "看看这个"})
    await client.post(path, json={"text": "看看这个", "image": "data:image/png;base64,aW1hZ2U="})
    entries = (await client.get(f"/api/conversations/{conversation}/messages")).json()
    assert len(entries) == 2
    assert all(not entry.get("image") for entry in entries)


async def test_active_image_formats_and_invalid_base64_are_refused(make_client: ClientFactory):
    client = make_client(FakeLLM())
    conversation = await start_conversation(client)
    for image in ("data:image/svg+xml;base64,PHN2Zy8+", "data:image/png;base64,%%%"):
        response = await client.post(
            f"/api/conversations/{conversation}/turns", json={"text": "图片", "image": image}
        )
        assert response.status_code == 422, image
    assert (await client.get(f"/api/conversations/{conversation}/messages")).json() == []


async def test_unconfigured_model_returns_setup_message_and_openers_require_login(
    make_client: ClientFactory, settings: Settings
):
    client = make_client(FakeLLM(), settings=replace(settings, chat_llm=LLMSettings("", "", "")))
    conversation = await start_conversation(client)
    response = await client.post(f"/api/conversations/{conversation}/turns", json={"text": "你好"})
    assert response.status_code == 503
    assert "CHAT_LLM_MODEL" in response.json()["detail"]
    visitor = make_client(FakeLLM(), user=None)
    assert (await visitor.get("/api/characters/mano/call-opener/speech")).status_code == 401


def test_higher_tiers_keep_the_same_out_of_line_criteria():
    for tier in (None, "cold", "distant", "trust", "close", "intimate", "love"):
        assert questions_for(tier)[OUT_OF_LINE] == QUESTIONS[OUT_OF_LINE], tier


async def test_voice_message_availability_names_the_configured_provider(
    make_client: ClientFactory, settings: Settings
):
    soniox = make_client(FakeLLM(), settings=replace(settings, soniox_api_key="test-soniox-key"))
    unavailable = (await soniox.get("/api/voice")).json()
    assert unavailable["available"] is False
    assert "百炼" in unavailable["reason"] and "Soniox" in unavailable["reason"]
    bailian = make_client(
        FakeLLM(), settings=replace(settings, stt_provider="bailian", dashscope_api_key="test-bailian-key")
    )
    assert (await bailian.get("/api/voice")).json() == {"available": True, "reason": None}
