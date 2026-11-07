import { createRouter, createWebHashHistory } from "vue-router";
import { currentUser, getToken } from "./api";

const routes = [
  { path: "/", name: "products", component: () => import("./views/Products.vue") },
  {
    path: "/products/:id",
    name: "product",
    component: () => import("./views/ProductDetail.vue"),
  },
  { path: "/flash", name: "flash", component: () => import("./views/FlashSale.vue") },
  {
    path: "/cart",
    name: "cart",
    component: () => import("./views/Cart.vue"),
    meta: { auth: true },
  },
  {
    path: "/checkout",
    name: "checkout",
    component: () => import("./views/Checkout.vue"),
    meta: { auth: true },
  },
  {
    path: "/orders",
    name: "orders",
    component: () => import("./views/Orders.vue"),
    meta: { auth: true },
  },
  {
    path: "/addresses",
    name: "addresses",
    component: () => import("./views/Addresses.vue"),
    meta: { auth: true },
  },
  {
    path: "/admin",
    name: "admin",
    component: () => import("./views/Admin.vue"),
    meta: { auth: true, admin: true },
  },
  { path: "/login", name: "login", component: () => import("./views/Login.vue") },
  { path: "/:pathMatch(.*)*", redirect: "/" },
];

const router = createRouter({
  history: createWebHashHistory(),
  routes,
  scrollBehavior: () => ({ top: 0 }),
});

router.beforeEach((to) => {
  if (!to.meta.auth) return true;
  if (!getToken()) {
    return { name: "login", query: { redirect: to.fullPath } };
  }
  if (to.meta.admin && currentUser()?.role !== "ADMIN") {
    return { name: "products" };
  }
  return true;
});

export default router;
