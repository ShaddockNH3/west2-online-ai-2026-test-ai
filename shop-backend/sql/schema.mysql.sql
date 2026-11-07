-- 由 python -m scripts.gen_mysql_ddl 生成，请勿手改。
-- 适用于 MySQL 8.0+，字符集 utf8mb4。

CREATE DATABASE IF NOT EXISTS shop
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_0900_ai_ci;
USE shop;

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;
CREATE TABLE IF NOT EXISTS activities (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	name VARCHAR(64) NOT NULL, 
	type VARCHAR(16) NOT NULL, 
	status VARCHAR(16) NOT NULL, 
	description VARCHAR(255) NOT NULL, 
	starts_at DATETIME NOT NULL, 
	ends_at DATETIME NOT NULL, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS categories (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	name VARCHAR(64) NOT NULL, 
	sort_order INTEGER NOT NULL, 
	status VARCHAR(16) NOT NULL, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (name)
);

CREATE TABLE IF NOT EXISTS jobs (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	job_type VARCHAR(32) NOT NULL, 
	dedupe_key VARCHAR(96), 
	payload JSON NOT NULL, 
	status VARCHAR(16) NOT NULL, 
	attempts INTEGER NOT NULL, 
	max_attempts INTEGER NOT NULL, 
	next_run_at DATETIME NOT NULL, 
	locked_at DATETIME, 
	last_error VARCHAR(255) NOT NULL, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (dedupe_key)
);
CREATE INDEX ix_jobs_status_next ON jobs (status, next_run_at);
CREATE INDEX ix_jobs_job_type ON jobs (job_type);

CREATE TABLE IF NOT EXISTS users (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	username VARCHAR(64) NOT NULL, 
	password_hash VARCHAR(255) NOT NULL, 
	nickname VARCHAR(64) NOT NULL, 
	email VARCHAR(128), 
	phone VARCHAR(32), 
	`role` VARCHAR(16) NOT NULL, 
	status VARCHAR(16) NOT NULL, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (username)
);

CREATE TABLE IF NOT EXISTS warehouses (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	name VARCHAR(64) NOT NULL, 
	is_default BOOL NOT NULL, 
	created_at DATETIME NOT NULL, 
	PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS addresses (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	user_id INTEGER NOT NULL, 
	receiver VARCHAR(64) NOT NULL, 
	phone VARCHAR(32) NOT NULL, 
	detail VARCHAR(255) NOT NULL, 
	is_default BOOL NOT NULL, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
);
CREATE INDEX ix_addresses_user_id ON addresses (user_id);

CREATE TABLE IF NOT EXISTS auth_sessions (
	id VARCHAR(64) NOT NULL, 
	user_id INTEGER NOT NULL, 
	refresh_jti VARCHAR(64) NOT NULL, 
	expires_at DATETIME NOT NULL, 
	revoked_at DATETIME, 
	user_agent VARCHAR(255) NOT NULL, 
	created_at DATETIME NOT NULL, 
	last_used_at DATETIME, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
);
CREATE INDEX ix_auth_sessions_user_id ON auth_sessions (user_id);

CREATE TABLE IF NOT EXISTS orders (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	order_no VARCHAR(32) NOT NULL, 
	user_id INTEGER NOT NULL, 
	status VARCHAR(32) NOT NULL, 
	original_amount_cents INTEGER NOT NULL, 
	discount_amount_cents INTEGER NOT NULL, 
	total_amount_cents INTEGER NOT NULL, 
	receiver VARCHAR(64) NOT NULL, 
	phone VARCHAR(32) NOT NULL, 
	address_detail VARCHAR(255) NOT NULL, 
	request_id VARCHAR(64), 
	request_fingerprint VARCHAR(64) NOT NULL, 
	remark VARCHAR(255) NOT NULL, 
	expire_at DATETIME NOT NULL, 
	paid_at DATETIME, 
	shipped_at DATETIME, 
	cancelled_at DATETIME, 
	completed_at DATETIME, 
	cancel_reason VARCHAR(64) NOT NULL, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_order_user_request UNIQUE (user_id, request_id), 
	UNIQUE (order_no), 
	FOREIGN KEY(user_id) REFERENCES users (id)
);
CREATE INDEX ix_orders_user_id ON orders (user_id);
CREATE INDEX ix_orders_status_created ON orders (status, created_at);
CREATE INDEX ix_orders_user_status ON orders (user_id, status);

CREATE TABLE IF NOT EXISTS products (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	category_id INTEGER NOT NULL, 
	name VARCHAR(128) NOT NULL, 
	description TEXT NOT NULL, 
	cover_url VARCHAR(255) NOT NULL, 
	status VARCHAR(16) NOT NULL, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(category_id) REFERENCES categories (id)
);
CREATE INDEX ix_products_category_id ON products (category_id);
CREATE INDEX ix_products_status_id ON products (status, id);

CREATE TABLE IF NOT EXISTS fulfillments (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	fulfillment_no VARCHAR(32) NOT NULL, 
	order_id INTEGER NOT NULL, 
	order_no VARCHAR(32) NOT NULL, 
	status VARCHAR(16) NOT NULL, 
	receiver VARCHAR(64) NOT NULL, 
	phone VARCHAR(32) NOT NULL, 
	address_detail VARCHAR(255) NOT NULL, 
	items JSON NOT NULL, 
	tracking_no VARCHAR(64) NOT NULL, 
	attempts INTEGER NOT NULL, 
	last_error VARCHAR(255) NOT NULL, 
	shipped_at DATETIME, 
	completed_at DATETIME, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (fulfillment_no), 
	UNIQUE (order_id), 
	FOREIGN KEY(order_id) REFERENCES orders (id)
);
CREATE INDEX ix_fulfillments_order_no ON fulfillments (order_no);

CREATE TABLE IF NOT EXISTS order_items (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	order_id INTEGER NOT NULL, 
	sku_id INTEGER NOT NULL, 
	product_id INTEGER NOT NULL, 
	product_name VARCHAR(128) NOT NULL, 
	specs JSON NOT NULL, 
	original_unit_price_cents INTEGER NOT NULL, 
	unit_price_cents INTEGER NOT NULL, 
	quantity INTEGER NOT NULL, 
	subtotal_cents INTEGER NOT NULL, 
	discount_cents INTEGER NOT NULL, 
	activity_name VARCHAR(64) NOT NULL, 
	created_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(order_id) REFERENCES orders (id)
);
CREATE INDEX ix_order_items_order_id ON order_items (order_id);

CREATE TABLE IF NOT EXISTS payments (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	payment_no VARCHAR(32) NOT NULL, 
	order_id INTEGER NOT NULL, 
	order_no VARCHAR(32) NOT NULL, 
	user_id INTEGER NOT NULL, 
	amount_cents INTEGER NOT NULL, 
	status VARCHAR(16) NOT NULL, 
	channel VARCHAR(16) NOT NULL, 
	transaction_no VARCHAR(64) NOT NULL, 
	failure_reason VARCHAR(255) NOT NULL, 
	created_at DATETIME NOT NULL, 
	paid_at DATETIME, 
	PRIMARY KEY (id), 
	UNIQUE (payment_no), 
	FOREIGN KEY(order_id) REFERENCES orders (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
);
CREATE INDEX ix_payments_user_id ON payments (user_id);
CREATE INDEX ix_payments_order_id ON payments (order_id);
CREATE INDEX ix_payments_order_no ON payments (order_no);

CREATE TABLE IF NOT EXISTS skus (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	product_id INTEGER NOT NULL, 
	sku_code VARCHAR(64) NOT NULL, 
	specs JSON NOT NULL, 
	price_cents INTEGER NOT NULL, 
	status VARCHAR(16) NOT NULL, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(product_id) REFERENCES products (id), 
	UNIQUE (sku_code)
);
CREATE INDEX ix_skus_product_id ON skus (product_id);

CREATE TABLE IF NOT EXISTS activity_skus (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	activity_id INTEGER NOT NULL, 
	sku_id INTEGER NOT NULL, 
	activity_price_cents INTEGER NOT NULL, 
	sale_quota INTEGER, 
	sold_count INTEGER NOT NULL, 
	per_user_limit INTEGER, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_activity_sku UNIQUE (activity_id, sku_id), 
	FOREIGN KEY(activity_id) REFERENCES activities (id), 
	FOREIGN KEY(sku_id) REFERENCES skus (id)
);
CREATE INDEX ix_activity_skus_sku_id ON activity_skus (sku_id);
CREATE INDEX ix_activity_skus_activity_id ON activity_skus (activity_id);

CREATE TABLE IF NOT EXISTS cart_items (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	user_id INTEGER NOT NULL, 
	sku_id INTEGER NOT NULL, 
	quantity INTEGER NOT NULL, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_cart_user_sku UNIQUE (user_id, sku_id), 
	FOREIGN KEY(user_id) REFERENCES users (id), 
	FOREIGN KEY(sku_id) REFERENCES skus (id)
);
CREATE INDEX ix_cart_items_user_id ON cart_items (user_id);

CREATE TABLE IF NOT EXISTS flash_sale_requests (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	activity_id INTEGER NOT NULL, 
	sku_id INTEGER NOT NULL, 
	user_id INTEGER NOT NULL, 
	request_id VARCHAR(64) NOT NULL, 
	quantity INTEGER NOT NULL, 
	address_id INTEGER NOT NULL, 
	unit_price_cents INTEGER NOT NULL, 
	activity_name VARCHAR(64) NOT NULL, 
	status VARCHAR(16) NOT NULL, 
	order_no VARCHAR(32), 
	message VARCHAR(255) NOT NULL, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_flash_user_request UNIQUE (user_id, request_id), 
	FOREIGN KEY(activity_id) REFERENCES activities (id), 
	FOREIGN KEY(sku_id) REFERENCES skus (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
);
CREATE INDEX ix_flash_activity_sku_user ON flash_sale_requests (activity_id, sku_id, user_id);
CREATE INDEX ix_flash_sale_requests_user_id ON flash_sale_requests (user_id);

CREATE TABLE IF NOT EXISTS inventory (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	warehouse_id INTEGER NOT NULL, 
	sku_id INTEGER NOT NULL, 
	available INTEGER NOT NULL, 
	reserved INTEGER NOT NULL, 
	sold INTEGER NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_inventory_sku UNIQUE (warehouse_id, sku_id), 
	FOREIGN KEY(warehouse_id) REFERENCES warehouses (id), 
	FOREIGN KEY(sku_id) REFERENCES skus (id)
);
CREATE INDEX ix_inventory_sku_id ON inventory (sku_id);

CREATE TABLE IF NOT EXISTS inventory_logs (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	inventory_id INTEGER NOT NULL, 
	sku_id INTEGER NOT NULL, 
	order_no VARCHAR(32), 
	change_type VARCHAR(16) NOT NULL, 
	quantity INTEGER NOT NULL, 
	available_before INTEGER NOT NULL, 
	available_after INTEGER NOT NULL, 
	reason VARCHAR(255) NOT NULL, 
	created_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(inventory_id) REFERENCES inventory (id)
);
CREATE INDEX ix_inventory_logs_sku_id ON inventory_logs (sku_id);


SET FOREIGN_KEY_CHECKS = 1;

-- 默认仓库与默认门店数据由 scripts/init_db.py 写入。
