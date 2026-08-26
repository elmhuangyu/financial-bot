import { ref, watch } from "vue";

export interface ThemeOption {
  id: string;
  label: string;
  isDark: boolean;
}

export const THEMES: ThemeOption[] = [
  { id: "darkFinancial", label: "Financial Dark", isDark: true },
  { id: "light", label: "Clean Light", isDark: false },
  { id: "nord", label: "Nord Frost", isDark: false },
  { id: "corporate", label: "Corporate Light", isDark: false },
  { id: "emerald", label: "Emerald Light", isDark: false },
  { id: "night", label: "Deep Night", isDark: true },
  { id: "dim", label: "Dim Dark", isDark: true },
  { id: "dark", label: "Standard Dark", isDark: true },
];

const savedTheme = typeof localStorage !== "undefined" ? localStorage.getItem("fb_theme") : null;
const currentTheme = ref<string>(savedTheme || "darkFinancial");

// Apply theme to DOM immediately
if (typeof document !== "undefined") {
  document.documentElement.setAttribute("data-theme", currentTheme.value);
}

watch(currentTheme, (newTheme) => {
  if (typeof document !== "undefined") {
    document.documentElement.setAttribute("data-theme", newTheme);
  }
  if (typeof localStorage !== "undefined") {
    localStorage.setItem("fb_theme", newTheme);
  }
});

export function useTheme() {
  function setTheme(themeId: string) {
    currentTheme.value = themeId;
    if (typeof document !== "undefined") {
      document.documentElement.setAttribute("data-theme", themeId);
      (document.activeElement as HTMLElement)?.blur();
    }
  }

  return {
    themes: THEMES,
    currentTheme,
    setTheme,
  };
}
