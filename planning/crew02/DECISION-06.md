# Android TLS provider key permission, causal repair

Actual APK01 allowed mTLS did not handshake. The preserved Android13 logcat
(`evidence/crew02-runtime/tls02-logcat.txt`) reports Conscrypt prehashed
`NONEwithECDSA` signing rejected by AndroidKeyStore with incompatible digest
code -13. SHA256withECDSA possession proof passed but did not prove provider TLS
compatibility. All network negative claims from this attempt remain unqualified.

Contractor authorizes Builder to confirm and correct only the nonexportable
P256 key's permitted signing digests for Android TLS, keeping certificate
SHA256withECDSA, exact pins, TLS1.2/1.3 and default client hostname verification.
Existing key permissions cannot be rewritten. Use a versioned alias and explicit
UI key initialization plus out-of-band public trust reprovisioning, preserving
the original alias/key/public pins/audit. No silent identity change, key export,
old-evidence overwrite or claim of hardware attestation.

APK01 and failed sockets stay retained. Source amendment, independent targeted
review and a causally numbered development APK02 precede any new actual mTLS
attempt. This uses the existing three-build budget, no new SDK/image/dependency.
