import { afterEach, expect, it, vi } from "vitest";

import { speechState, stopSpeech, toggleSpeech } from "./messageSpeech";

class TestAudio extends EventTarget {
  src: string;
  pause = vi.fn();
  rejectPlay: (error: Error) => void = () => {};

  constructor(src: string) {
    super();
    this.src = src;
    players.push(this);
  }

  play() {
    return new Promise<void>((_resolve, reject) => {
      this.rejectPlay = reject;
    });
  }
}

const players: TestAudio[] = [];

afterEach(() => {
  stopSpeech();
  players.length = 0;
  vi.unstubAllGlobals();
});

it("keeps the new reply playing when the previous player rejects or reports late events", async () => {
  vi.stubGlobal("Audio", TestAudio);
  toggleSpeech(12);
  const first = players[0];
  toggleSpeech(13);
  const second = players[1];
  first.rejectPlay(new Error("playback interrupted"));
  first.dispatchEvent(new Event("playing"));
  first.dispatchEvent(new Event("error"));
  await Promise.resolve();
  expect(speechState()).toEqual({ messageId: 13, phase: "loading" });
  expect(second.pause).not.toHaveBeenCalled();
  second.dispatchEvent(new Event("playing"));
  expect(speechState()).toEqual({ messageId: 13, phase: "playing" });
  second.dispatchEvent(new Event("ended"));
  expect(speechState()).toBeNull();
});
