"""全局配置。"""

DATABASE_URL = "sqlite:///./trading.db"

# 默认账户
DEFAULT_INITIAL_CAPITAL = 1_000_000.0

# 交易费用（A 股规则）
COMMISSION_RATE = 0.00025       # 佣金万 2.5
COMMISSION_MIN = 5.0            # 最低佣金 5 元
STAMP_TAX_RATE = 0.0005         # 印花税（仅卖出）
TRANSFER_FEE_RATE = 0.00001     # 过户费

# 排除的板块代码前缀
EXCLUDED_PREFIXES = ("300", "301", "688", "689")

# 扫描触发时间（交易日收盘后）
SCAN_HOUR = 15
SCAN_MINUTE = 5

# 当前券商模式：paper（模拟盘）/ live（实盘，未接入）
BROKER_TYPE = "paper"
