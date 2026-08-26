import { ref, watch } from "vue";

export interface ThemeOption {
  id: string;
  label: string;
  isDark: boolean;
}

export const THEMES: ThemeOption[] = [
  { id: "business", label: "Business Dark", isDark: true },
  { id: "forest", label: "Forest Dark", isDark: true },
  { id: "night", label: "Deep Night", isDark: true },
  { id: "dim", label: "Dim Dark", isDark: true },
  { id: "dark", label: "Standard Dark", isDark: true },
  { id: "emerald", label: "Emerald Light", isDark: false },
  { id: "nord", label: "Nord Frost", isDark: false },
  { id: "corporate", label: "Corporate Light", isDark: false },
  { id: "light", label: "Clean Light", isDark: false },
];

function getInitialTheme(): string {
  if (typeof localStorage !== "undefined") {
    const saved = localStorage.getItem("fb_theme");
    if (saved && THEMES.some((t) => t.id === saved)) {
      return saved;
    }
  }
  return "business";
}

const currentTheme = ref<string>(getInitialTheme());

// Apply theme to DOM immediately upon module import
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
    if (!THEMES.some((t) => t.id === themeId)) return;
    currentTheme.value = themeId;
    if (typeof document !== "undefined") {
      document.documentElement.setAttribute("data-theme", themeId);
    }
    if (typeof localStorage !== "undefined") {
      localStorage.setItem("fb_theme", themeId);
    }
  }

  function toggleTheme() {
    const currentOpt = THEMES.find((t) => t.id === currentTheme.value);
    const isDark = currentOpt ? currentOpt.isDark : true;
    setTheme(isDark ? "light" : "business");
  }

  return {
    themes: THEMES,
    currentTheme,
    setTheme,
    toggleTheme,
  };
}
