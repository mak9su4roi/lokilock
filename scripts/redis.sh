postinit() {
    pong=1
    until [ ${pong} -eq 0 ]; do
        sleep 1; 
        redis-cli ping
        pong=$?
    done
    redis-cli FT.CREATE idx SCHEMA \
        vector VECTOR FLAT 6 TYPE FLOAT32 DIM 1024 DISTANCE_METRIC COSINE \
        user TEXT \
        lock TEXT
}
postinit &
/entrypoint.sh