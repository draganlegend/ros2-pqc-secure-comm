std_msgs/Header header
geometry_msgs/Twist command

uint8 payload_version
string payload_schema

builtin_interfaces/Time source_stamp
uint64 sequence
uint32 ttl_ms

string source_id
string key_id

uint8 sig_scheme
uint8 hash_scheme

uint8 SIG_SCHEME_UNKNOWN=0
uint8 SIG_SCHEME_ML_DSA_44=1

uint8 HASH_SCHEME_UNKNOWN=0
uint8 HASH_SCHEME_SHA256=1

uint8[] payload_digest
uint8[] signature
