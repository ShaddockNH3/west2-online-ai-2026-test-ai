export const themeOverrides = {
  common: {
    primaryColor: "#1d4ed8",
    primaryColorHover: "#2563eb",
    primaryColorPressed: "#1e40af",
    primaryColorSuppl: "#2563eb",
    infoColor: "#1d4ed8",
    successColor: "#0f9d58",
    warningColor: "#d97706",
    errorColor: "#d92d20",
    bodyColor: "#f4f6fa",
    cardColor: "#ffffff",
    modalColor: "#ffffff",
    popoverColor: "#ffffff",
    borderRadius: "10px",
    fontSize: "14px",
    textColorBase: "#0f172a",
    textColor1: "#0f172a",
    textColor2: "#334155",
    textColor3: "#64748b",
    borderColor: "#e2e8f0",
    dividerColor: "#eef2f7",
    tableHeaderColor: "#f1f5f9",
  },
  Card: {
    borderColor: "#e8edf5",
    color: "#ffffff",
    titleFontWeight: "600",
  },
  DataTable: {
    thColor: "#f1f5f9",
    thTextColor: "#334155",
    tdTextColor: "#1f2937",
    borderColor: "#e8edf5",
    thFontWeight: "600",
  },
  Tag: {
    borderRadius: "6px",
  },
  Button: {
    fontWeight: "500",
  },
  Menu: {
    itemTextColorActive: "#1d4ed8",
    itemTextColorActiveHover: "#1d4ed8",
    itemTextColorHover: "#1d4ed8",
    itemIconColorActive: "#1d4ed8",
    itemIconColorActiveHover: "#1d4ed8",
  },
};

export const statusText = {
  PENDING_PAYMENT: "待支付",
  PAID: "已支付",
  SHIPPED: "已发货",
  COMPLETED: "已完成",
  CANCELLED: "已取消",
};

export const statusType = {
  PENDING_PAYMENT: "warning",
  PAID: "info",
  SHIPPED: "primary",
  COMPLETED: "success",
  CANCELLED: "default",
};

export const fulfillmentText = {
  PENDING: "待备货",
  READY_TO_SHIP: "待发货",
  SHIPPED: "已发货",
  COMPLETED: "已完成",
  EXCEPTION: "异常",
};

export const flashText = {
  QUEUED: "排队中",
  SUCCEEDED: "抢购成功",
  FAILED: "抢购失败",
  REJECTED: "未通过",
};

export const flashType = {
  QUEUED: "warning",
  SUCCEEDED: "success",
  FAILED: "error",
  REJECTED: "default",
};
