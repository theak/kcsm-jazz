// Bluetooth speaker mode. Each slot (0 = A, 1 = B) remembers one device, and
// the box reconnects to that slot's device when the slot is started.
#pragma once

bool btSlotHasDevice(int slot);
void btStart(int slot, const char* name);  // plays through the speaker (speakerBegin first)
bool btIsConnected();
bool btIsPlaying();
void btRememberDevice(int slot);  // saves the connected device to the slot
void btDisconnect();
