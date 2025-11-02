log_path = "/Users/grady/workplace/software/nginx/logs/access.log"

with open(log_path, mode="r", encoding="utf-8") as f:
    # print(sum(1 for _ in f))
    for line in f:
        print(line)
