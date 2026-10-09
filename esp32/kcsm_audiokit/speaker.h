// The I2S output whenever the radio library isn't using it: voice prompts at
// startup, and everything in Bluetooth mode.
#pragma once
#include <stddef.h>
#include <stdint.h>
#include "prompts.h"

void speakerBegin();  // 44.1 kHz, 16-bit stereo
void speakerEnd();    // releases the I2S port so the radio library can take it
void speakerSetSampleRate(int rate);

// 16-bit stereo PCM. Dropped while a prompt is playing so the two don't overlap.
size_t speakerWrite(const uint8_t* data, size_t len);

// Blocks until the prompt has played.
void say(PromptId id);
