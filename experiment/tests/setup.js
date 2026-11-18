// Node 18 has no global Web Crypto; Node 20+ does. Provide it so tests run on both.
import { webcrypto } from "node:crypto";

if (!globalThis.crypto) globalThis.crypto = webcrypto;
