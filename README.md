# tiktokvideo



测试服执行：
```
docker pull yudengc/public:tiktokvideo
docker run -d --restart=always --name=tiktokvideo -p 8000:80 yudengc/public:tiktokvideo
特别的, 要使用本地目录(如用自己的分支，不用master)的时候, 执行：
docker run -d --restart=always --name=tiktokvideo -p 8000:80 -v /我的目录:/selection yudengc/public:tiktokvideo
# docker ps -a 查看等待完全启动完毕后执行model初始化
docker exec tiktokvideo manage init test [schemas]
docker restart tiktokvideo
这样8000端口就可以用了
post http://127.0.0.1:8000/api/v1/user/test/ 试试把
```

正式服
```
正式服通常需要额外定义redis，pgsql的地址，
部署方式下个版本更新:

修改env配置文件, 如
docker exec tiktokvideo manage config --REDIS_BACKEND="127.0.0.1" --DATABASE_HOST="127.0.0.1"

更新代码
docker exec tiktokvideo manage update master

安装依赖
docker exec tiktokvideo manage update requirement
docker restart tiktokvideo
```


**以上的manage命令均可以在 tools/manage/的目录自定义写脚本,如config.sh对应config命令**

```
tips:

docker engine 配置
{
  "registry-mirrors": [
    "https://docker.mirrors.ustc.edu.cn"
  ],
  "insecure-registries": [],
  "debug": true,
  "experimental": false,
  "ipv6": true,
  "fixed-cidr-v6": "2001:db8:1::/64"
}

```
