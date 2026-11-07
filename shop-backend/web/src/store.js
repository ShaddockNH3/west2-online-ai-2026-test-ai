import { reactive } from "vue";
import { clearAuth, currentUser, getToken, http } from "./api";

export const store = reactive({
  user: currentUser(),
  cartCount: 0,
  checkoutIds: [],
});

export function syncUser() {
  store.user = currentUser();
}

export async function refreshCart() {
  if (!getToken()) {
    store.cartCount = 0;
    return;
  }
  try {
    const cart = await http.get("/cart/items");
    store.cartCount = cart.totalQuantity || 0;
  } catch {
    store.cartCount = 0;
  }
}

export function signOut() {
  clearAuth();
  store.user = null;
  store.cartCount = 0;
  store.checkoutIds = [];
}
