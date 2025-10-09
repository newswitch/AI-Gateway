FROM openresty/openresty:alpine

# 安装必要的工具（合并RUN命令减少层数）
RUN apk add --no-cache \
    curl \
    bash \
    git \
    build-base \
    lua-resty-openssl \
    && rm -rf /var/cache/apk/*

# 安装lua-resty-http（一次性安装所有依赖）
RUN cd /tmp && \
    git clone https://github.com/ledgetech/lua-resty-http.git && \
    cd lua-resty-http && \
    make install PREFIX=/usr/local/openresty && \
    find lib/resty -name "*.lua" -exec cp {} /usr/local/openresty/lualib/resty/ \; && \
    rm -rf /tmp/lua-resty-http

# 如果apk安装的openssl模块位置不对，从源码编译
RUN if [ ! -d "/usr/local/openresty/lualib/resty/openssl" ]; then \
    cd /tmp && \
    git clone https://github.com/fffonion/lua-resty-openssl.git && \
    cd lua-resty-openssl && \
    make install PREFIX=/usr/local/openresty && \
    find lib/resty -name "*.lua" -exec cp {} /usr/local/openresty/lualib/resty/ \; && \
    find lib/resty -name "*.so" -exec cp {} /usr/local/openresty/lualib/resty/ \; && \
    rm -rf /tmp/lua-resty-openssl; \
    fi

# 将openssl模块复制到正确的位置（如果需要）
RUN if [ -d "/usr/share/lua/common/resty/openssl" ]; then \
    cp -r /usr/share/lua/common/resty/openssl /usr/local/openresty/lualib/resty/; \
    fi

# 设置工作目录和创建必要目录（合并命令）
WORKDIR /usr/local/openresty/nginx
RUN mkdir -p /var/log/nginx && \
    chown -R nobody:nobody /var/log/nginx

# 复制配置文件（不经常变化，放在前面）
COPY conf/nginx.conf /usr/local/openresty/nginx/conf/nginx.conf

# 复制Lua脚本（经常变化，放在最后）
COPY conf/lua/ /usr/local/openresty/nginx/conf/lua/

# 暴露端口
EXPOSE 80

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:80/health || exit 1

# 启动OpenResty
CMD ["/usr/local/openresty/bin/openresty", "-g", "daemon off;"] 