-- =========================================================
-- BANKING SYSTEM - DATABASE SCHEMA (MySQL 8.0+)
-- =========================================================
create database BankSystem;
use BankSystem;

SET NAMES utf8mb4;

-- ---------------------------------------------------------
-- 1. USERS //
-- ---------------------------------------------------------
CREATE TABLE users (
    user_id         BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    full_name       VARCHAR(150)  NOT NULL,
    email           VARCHAR(150)  NOT NULL UNIQUE,
    phone_number    VARCHAR(20)   NOT NULL UNIQUE,
    national_id     VARCHAR(30)   NOT NULL UNIQUE,
    date_of_birth   DATE          NOT NULL,
    address         VARCHAR(255),
    pin_hash        VARCHAR(255),
    -- password_hash/salt and master_key live in user_security below
    kyc_status      VARCHAR(20)   NOT NULL DEFAULT 'pending'
                        CHECK (kyc_status IN ('pending','verified','rejected')),
    role            VARCHAR(20)   NOT NULL DEFAULT 'customer'
                        CHECK (role IN ('customer','admin','support')),
    status          VARCHAR(20)   NOT NULL DEFAULT 'active'
                        CHECK (status IN ('active','frozen','closed')),
    created_at      TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- ---------------------------------------------------------
-- 1b. USER SECURITY //
-- ---------------------------------------------------------
CREATE TABLE user_security (
    user_id             BIGINT UNSIGNED PRIMARY KEY,
    password_hash       VARCHAR(255) NOT NULL,
    -- password_salt       VARCHAR(64)  NOT NULL,
    master_key_hash     VARCHAR(255),
    -- master_key_salt     VARCHAR(64),
    failed_login_count  INT UNSIGNED NOT NULL DEFAULT 0,
    locked_until        TIMESTAMP NULL,
    last_login_at       TIMESTAMP NULL,
    updated_at          TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                            ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_security_user FOREIGN KEY (user_id)
        REFERENCES users(user_id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ---------------------------------------------------------
-- 2. ACCOUNTS //
-- ---------------------------------------------------------
CREATE TABLE accounts (
    account_id      BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id         BIGINT UNSIGNED NOT NULL,
    iban            VARCHAR(34)   NOT NULL UNIQUE,
    account_type    VARCHAR(20)   NOT NULL DEFAULT 'checking'
                        CHECK (account_type IN ('checking','savings')),
    currency        CHAR(3)       NOT NULL DEFAULT 'EUR',
    balance         DECIMAL(14,2) NOT NULL DEFAULT 0.00,
    overdraft_limit DECIMAL(14,2) NOT NULL DEFAULT 1000.00,
    status          VARCHAR(20)   NOT NULL DEFAULT 'active'
                        CHECK (status IN ('active','frozen','closed')),
    created_at      TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_accounts_user FOREIGN KEY (user_id)
        REFERENCES users(user_id) ON DELETE RESTRICT,
    CONSTRAINT chk_balance_overdraft CHECK (balance >= -overdraft_limit)
) ENGINE=InnoDB;

-- ---------------------------------------------------------
-- 3. CARDS //
-- ---------------------------------------------------------
CREATE TABLE cards (
    card_id         BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    account_id      BIGINT UNSIGNED NOT NULL,
    card_number_hash VARCHAR(255) NOT NULL UNIQUE,
    last_four       CHAR(4)       NOT NULL,
    card_type       VARCHAR(10)   NOT NULL CHECK (card_type IN ('debit','credit')),
    expiry_date     DATE          NOT NULL,
    daily_limit     DECIMAL(10,2) NOT NULL DEFAULT 400.00,
    status          VARCHAR(20)   NOT NULL DEFAULT 'active'
                        CHECK (status IN ('active','blocked', 'frozen','expired')),
    created_at      TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    cvv             CHAR(3)		  NOT NULL AUTO_INCREMENT,
    CONSTRAINT fk_cards_account FOREIGN KEY (account_id)
        REFERENCES accounts(account_id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ---------------------------------------------------------
-- 4. MBWAY LINKS
-- ---------------------------------------------------------
CREATE TABLE mbway_links (
    mbway_id        BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    account_id      BIGINT UNSIGNED NOT NULL,
    phone_number    VARCHAR(20)   NOT NULL UNIQUE,
    status          VARCHAR(20)   NOT NULL DEFAULT 'active'
                        CHECK (status IN ('active','inactive')),
    created_at      TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_mbway_account FOREIGN KEY (account_id)
        REFERENCES accounts(account_id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ---------------------------------------------------------
-- 5. TRANSACTIONS //
-- ---------------------------------------------------------
CREATE TABLE transactions (
    transaction_id  BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    from_account_id BIGINT UNSIGNED NULL,
    to_account_id   BIGINT UNSIGNED NULL,
    amount          DECIMAL(14,2) NOT NULL CHECK (amount > 0),
    currency        CHAR(3)       NOT NULL DEFAULT 'EUR',
    transaction_type VARCHAR(20)  NOT NULL
                        CHECK (transaction_type IN
                            ('deposit','withdrawal_card','withdrawal_mbway',
                             'transfer_iban','payment_code','fee','interest')),
    status          VARCHAR(20)   NOT NULL DEFAULT 'pending'
                        CHECK (status IN ('pending','completed','failed','reversed')),
    reference       VARCHAR(100),
    description     VARCHAR(255),
    idempotency_key VARCHAR(64)   UNIQUE,
    created_at      TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    processed_at    TIMESTAMP NULL,
    CONSTRAINT fk_tx_from FOREIGN KEY (from_account_id) REFERENCES accounts(account_id),
    CONSTRAINT fk_tx_to   FOREIGN KEY (to_account_id)   REFERENCES accounts(account_id)
) ENGINE=InnoDB;
CREATE INDEX idx_transactions_from ON transactions(from_account_id);
CREATE INDEX idx_transactions_to   ON transactions(to_account_id);
CREATE INDEX idx_transactions_created ON transactions(created_at);

-- ---------------------------------------------------------
-- 6. PAYMENT CODES //
-- ---------------------------------------------------------
CREATE TABLE payment_codes (
    code            VARCHAR(20)   PRIMARY KEY,
    account_id      BIGINT UNSIGNED NOT NULL,
    amount          DECIMAL(14,2) NOT NULL CHECK (amount > 0),
    description     VARCHAR(255),
    is_used         BOOLEAN       NOT NULL DEFAULT FALSE,
    expires_at      TIMESTAMP     NOT NULL,
    created_at      TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_paycode_account FOREIGN KEY (account_id) REFERENCES accounts(account_id)
) ENGINE=InnoDB;

-- ---------------------------------------------------------
-- 7. SCHEDULED / RECURRING PAYMENTS //
-- ---------------------------------------------------------
CREATE TABLE scheduled_payments (
    scheduled_id    BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    account_id      BIGINT UNSIGNED NOT NULL,
    payee_iban      VARCHAR(34),
    amount          DECIMAL(14,2) NOT NULL CHECK (amount > 0),
    frequency       VARCHAR(20)   NOT NULL DEFAULT 'once'
                        CHECK (frequency IN ('once','weekly','monthly','yearly')),
    next_due_date   DATE          NOT NULL,
    status          VARCHAR(20)   NOT NULL DEFAULT 'active'
                        CHECK (status IN ('active','paused','completed','failed')),
    description     VARCHAR(255),
    created_at      TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_sched_account FOREIGN KEY (account_id) REFERENCES accounts(account_id)
) ENGINE=InnoDB;

-- ---------------------------------------------------------
-- 8. MARKET DATA + AI RECOMMENDATIONS
-- ---------------------------------------------------------
CREATE TABLE market_assets (
    asset_id        BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    symbol          VARCHAR(15)   NOT NULL UNIQUE,
    name            VARCHAR(100)  NOT NULL,
    asset_type      VARCHAR(20)   NOT NULL DEFAULT 'stock'
                        CHECK (asset_type IN ('stock','etf','crypto'))
) ENGINE=InnoDB;

CREATE TABLE market_prices (
    price_id        BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    asset_id        BIGINT UNSIGNED NOT NULL,
    price           DECIMAL(14,4) NOT NULL,
    fetched_at      TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_price_asset FOREIGN KEY (asset_id) REFERENCES market_assets(asset_id)
) ENGINE=InnoDB;
CREATE INDEX idx_market_prices_asset_time ON market_prices(asset_id, fetched_at);

CREATE TABLE ai_recommendations (
    recommendation_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id         BIGINT UNSIGNED NOT NULL,
    asset_id        BIGINT UNSIGNED NOT NULL,
    action          VARCHAR(10)   NOT NULL CHECK (action IN ('buy','sell','hold')),
    confidence      DECIMAL(4,3),
    reasoning       TEXT,
    created_at      TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_rec_user  FOREIGN KEY (user_id)  REFERENCES users(user_id),
    CONSTRAINT fk_rec_asset FOREIGN KEY (asset_id) REFERENCES market_assets(asset_id)
) ENGINE=InnoDB;

-- ---------------------------------------------------------
-- 9. AUDIT LOG
-- ---------------------------------------------------------
CREATE TABLE audit_log (
    log_id          BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id         BIGINT UNSIGNED NULL,
    action          VARCHAR(100)  NOT NULL,
    ip_address      VARCHAR(45),
    details         JSON,
    created_at      TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_audit_user FOREIGN KEY (user_id) REFERENCES users(user_id)
) ENGINE=InnoDB;

-- ---------------------------------------------------------
-- 10. SESSIONS
-- ---------------------------------------------------------
CREATE TABLE sessions (
    session_id      CHAR(36)      NOT NULL PRIMARY KEY, -- generate UUID in Python (uuid.uuid4())
    user_id         BIGINT UNSIGNED NOT NULL,
    token_hash      VARCHAR(255)  NOT NULL,
    created_at      TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at      TIMESTAMP     NOT NULL,
    revoked         BOOLEAN       NOT NULL DEFAULT FALSE,
    CONSTRAINT fk_session_user FOREIGN KEY (user_id)
        REFERENCES users(user_id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- =========================================================
-- USEFUL VIEWS
-- =========================================================

CREATE VIEW user_account_overview AS
SELECT u.user_id, u.full_name, u.email, a.account_id, a.iban, a.balance, a.currency, a.status
FROM users u
JOIN accounts a ON a.user_id = u.user_id;

CREATE VIEW upcoming_payments AS
SELECT sp.scheduled_id, a.user_id, sp.account_id, sp.payee_iban, sp.amount, sp.next_due_date
FROM scheduled_payments sp
JOIN accounts a ON a.account_id = sp.account_id
WHERE sp.status = 'active' AND sp.next_due_date <= CURDATE() + INTERVAL 7 DAY;
