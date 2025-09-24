FROM openresty/openresty:alpine-fat

# 安装必要的工具
RUN apk add --no-cache \
    curl \
    bash \
    git \
    build-base \
    && rm -rf /var/cache/apk/*

# 安装lua-resty-http
RUN cd /tmp && \
    git clone https://github.com/ledgetech/lua-resty-http.git && \
    cd lua-resty-http && \
    make install PREFIX=/usr/local/openresty && \
    find lib/resty -name "*.lua" -exec cp {} /usr/local/openresty/lualib/resty/ \; && \
    rm -rf /tmp/lua-resty-http

# 安装lua-resty-openssl（Alpine Linux使用apk）
RUN apk add --no-cache lua-resty-openssl || \
    (cd /tmp && \
    git clone https://github.com/fffonion/lua-resty-openssl.git && \
    cd lua-resty-openssl && \
    make install PREFIX=/usr/local/openresty && \
    find lib/resty -name "*.lua" -exec cp {} /usr/local/openresty/lualib/resty/ \; && \
    find lib/resty -name "*.so" -exec cp {} /usr/local/openresty/lualib/resty/ \; && \
    rm -rf /tmp/lua-resty-openssl)

# 将openssl模块复制到正确的位置
RUN if [ -d "/usr/share/lua/common/resty/openssl" ]; then \
    cp -r /usr/share/lua/common/resty/openssl /usr/local/openresty/lualib/resty/; \
    fi

# 检查已安装的模块
RUN ls -la /usr/local/openresty/lualib/resty/ || echo "Checking resty modules"

# 设置工作目录
WORKDIR /usr/local/openresty/nginx

# 复制配置文件
COPY conf/nginx.conf /usr/local/openresty/nginx/conf/nginx.conf

# 复制Lua脚本
COPY conf/lua/ /usr/local/openresty/nginx/conf/lua/

# 创建日志目录
RUN mkdir -p /var/log/nginx

# 设置权限
RUN chown -R nobody:nobody /var/log/nginx

# 暴露端口
EXPOSE 80

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:80/health || exit 1

# 启动OpenResty
CMD ["/usr/local/openresty/bin/openresty", "-g", "daemon off;"] 