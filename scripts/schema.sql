-- DataPilot 数据层 Schema
-- 场景：电商销售数据分析（支撑自然语言数据分析 Agent）

CREATE TABLE categories (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL COMMENT '类目名称',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
) COMMENT='商品类目表';

CREATE TABLE products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    category_id INT NOT NULL COMMENT '所属类目',
    name VARCHAR(100) NOT NULL COMMENT '商品名称',
    brand VARCHAR(50) NOT NULL COMMENT '品牌',
    price DECIMAL(10,2) NOT NULL COMMENT '当前售价',
    cost_price DECIMAL(10,2) NOT NULL COMMENT '成本价',
    launch_date DATE NOT NULL COMMENT '上架日期',
    status ENUM('on_sale','off_sale') DEFAULT 'on_sale' COMMENT '销售状态',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_category (category_id),
    CONSTRAINT fk_products_category FOREIGN KEY (category_id) REFERENCES categories(id)
) COMMENT='商品表';

CREATE TABLE customers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL COMMENT '客户姓名',
    gender ENUM('M','F') COMMENT '性别',
    province VARCHAR(30) COMMENT '省份',
    city VARCHAR(30) COMMENT '城市',
    channel VARCHAR(20) COMMENT '注册渠道：APP/小程序/网页/线下门店',
    register_date DATE COMMENT '注册日期',
    INDEX idx_region (province, city)
) COMMENT='客户表';

CREATE TABLE promotions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL COMMENT '活动名称',
    start_date DATE NOT NULL COMMENT '开始日期',
    end_date DATE NOT NULL COMMENT '结束日期',
    discount_rate DECIMAL(4,2) NOT NULL COMMENT '折扣率，0.85=85折',
    scope_type ENUM('all','category','product') NOT NULL COMMENT '适用范围',
    scope_id INT COMMENT 'scope为category时是类目ID，product时是商品ID，all时为NULL',
    INDEX idx_dates (start_date, end_date)
) COMMENT='促销活动表';

CREATE TABLE price_changes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    product_id INT NOT NULL COMMENT '商品ID',
    change_date DATE NOT NULL COMMENT '调价日期',
    old_price DECIMAL(10,2) NOT NULL,
    new_price DECIMAL(10,2) NOT NULL,
    reason VARCHAR(100) COMMENT '调价原因',
    INDEX idx_product (product_id),
    INDEX idx_date (change_date)
) COMMENT='商品调价记录表';

CREATE TABLE orders (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    order_no VARCHAR(32) NOT NULL UNIQUE COMMENT '订单号',
    customer_id INT NOT NULL COMMENT '下单客户',
    order_time DATETIME NOT NULL COMMENT '下单时间',
    status ENUM('completed','refunded','cancelled') DEFAULT 'completed' COMMENT '订单状态',
    payment_method VARCHAR(20) COMMENT '支付方式',
    total_amount DECIMAL(12,2) NOT NULL COMMENT '实付金额',
    INDEX idx_customer (customer_id),
    INDEX idx_order_time (order_time),
    INDEX idx_status (status)
) COMMENT='订单表';

CREATE TABLE order_items (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    order_id BIGINT NOT NULL COMMENT '订单ID',
    product_id INT NOT NULL COMMENT '商品ID',
    quantity INT NOT NULL COMMENT '购买数量',
    unit_price DECIMAL(10,2) NOT NULL COMMENT '成交单价（已含促销折扣）',
    discount_amount DECIMAL(10,2) DEFAULT 0 COMMENT '优惠金额',
    INDEX idx_order (order_id),
    INDEX idx_product (product_id),
    CONSTRAINT fk_items_order FOREIGN KEY (order_id) REFERENCES orders(id),
    CONSTRAINT fk_items_product FOREIGN KEY (product_id) REFERENCES products(id)
) COMMENT='订单明细表';

CREATE TABLE product_daily_stats (
    product_id INT NOT NULL COMMENT '商品ID',
    stat_date DATE NOT NULL COMMENT '统计日期',
    views INT DEFAULT 0 COMMENT '浏览量',
    cart_adds INT DEFAULT 0 COMMENT '加购次数',
    orders_count INT DEFAULT 0 COMMENT '成交件数',
    sales_amount DECIMAL(12,2) DEFAULT 0 COMMENT '销售额',
    refund_count INT DEFAULT 0 COMMENT '退款件数',
    stock_qty INT DEFAULT 0 COMMENT '当日库存',
    PRIMARY KEY (product_id, stat_date),
    INDEX idx_date (stat_date)
) COMMENT='商品每日经营指标表';

CREATE TABLE reviews (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    product_id INT NOT NULL COMMENT '商品ID',
    customer_id INT NOT NULL COMMENT '评价客户',
    rating TINYINT NOT NULL COMMENT '评分1-5',
    content VARCHAR(500) COMMENT '评价内容',
    review_time DATETIME NOT NULL COMMENT '评价时间',
    INDEX idx_product (product_id),
    INDEX idx_time (review_time),
    INDEX idx_rating (rating)
) COMMENT='商品评价表';
