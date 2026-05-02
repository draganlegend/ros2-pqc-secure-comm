std_msgs/Header header

bool ok
uint8 result_code
string reason

string source_id
string key_id
uint64 sequence

uint64 verify_ns
uint64 age_ns

uint8 RESULT_OK=0
uint8 RESULT_SCHEMA_ERROR=1
uint8 RESULT_ALG_UNSUPPORTED=2
uint8 RESULT_DIGEST_MISMATCH=3
uint8 RESULT_SIG_INVALID=4
uint8 RESULT_REPLAY=5
uint8 RESULT_EXPIRED=6
uint8 RESULT_KEY_NOT_TRUSTED=7
uint8 RESULT_INTERNAL_ERROR=8
