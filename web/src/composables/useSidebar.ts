import { ref } from "vue";

const isSidebarCollapsed = ref<boolean>(false);

export function useSidebar() {
  function toggleSidebar() {
    isSidebarCollapsed.value = !isSidebarCollapsed.value;
  }

  function setSidebar(collapsed: boolean) {
    isSidebarCollapsed.value = collapsed;
  }

  return {
    isSidebarCollapsed,
    toggleSidebar,
    setSidebar,
  };
}
