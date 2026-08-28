import mermaid from "mermaid";
import { formatHex, parse, oklch, type Color } from "culori";
import { THEMES } from "../composables/useTheme";

const DEFAULT_VIBRANT_PALETTE = [
  "#0ea5e9", // Sky / Info
  "#22c55e", // Emerald / Success
  "#f59e0b", // Amber / Warning
  "#8b5cf6", // Violet / Secondary
  "#f43f5e", // Rose / Error
  "#ec4899", // Pink / Accent
  "#14b8a6", // Teal
  "#f97316", // Orange
  "#3b82f6", // Blue
  "#84cc16", // Lime
  "#d946ef", // Fuchsia
  "#06b6d4", // Cyan
];

const THEME_PALETTES: Record<
  string,
  {
    isDark: boolean;
    base100: string;
    base200: string;
    base300: string;
    baseContent: string;
    baseBorder: string;
    primary: string;
    secondary: string;
    accent: string;
    info: string;
    success: string;
    warning: string;
    error: string;
  }
> = {
  business: {
    isDark: true,
    base100: "#1e293b",
    base200: "#161e2e",
    base300: "#0f172a",
    baseContent: "#f8fafc",
    baseBorder: "#38bdf8",
    primary: "#38bdf8",
    secondary: "#818cf8",
    accent: "#f472b6",
    info: "#38bdf8",
    success: "#34d399",
    warning: "#fbbf24",
    error: "#f87171",
  },
  forest: {
    isDark: true,
    base100: "#1b241e",
    base200: "#141c16",
    base300: "#0e1410",
    baseContent: "#f0fdf4",
    baseBorder: "#34d399",
    primary: "#34d399",
    secondary: "#2dd4bf",
    accent: "#a78bfa",
    info: "#38bdf8",
    success: "#34d399",
    warning: "#fbbf24",
    error: "#f87171",
  },
  night: {
    isDark: true,
    base100: "#1e293b",
    base200: "#0f172a",
    base300: "#090d16",
    baseContent: "#f8fafc",
    baseBorder: "#38bdf8",
    primary: "#38bdf8",
    secondary: "#818cf8",
    accent: "#f472b6",
    info: "#38bdf8",
    success: "#34d399",
    warning: "#fbbf24",
    error: "#f87171",
  },
  dim: {
    isDark: true,
    base100: "#2a303c",
    base200: "#222731",
    base300: "#1a1e27",
    baseContent: "#f8fafc",
    baseBorder: "#a3e635",
    primary: "#a3e635",
    secondary: "#facc15",
    accent: "#38bdf8",
    info: "#38bdf8",
    success: "#4ade80",
    warning: "#facc15",
    error: "#f87171",
  },
  dark: {
    isDark: true,
    base100: "#242b35",
    base200: "#1d232a",
    base300: "#15191e",
    baseContent: "#f8fafc",
    baseBorder: "#a78bfa",
    primary: "#a78bfa",
    secondary: "#f472b6",
    accent: "#38bdf8",
    info: "#38bdf8",
    success: "#34d399",
    warning: "#fbbf24",
    error: "#f87171",
  },
  emerald: {
    isDark: false,
    base100: "#ffffff",
    base200: "#f8fafc",
    base300: "#e2e8f0",
    baseContent: "#0f172a",
    baseBorder: "#059669",
    primary: "#059669",
    secondary: "#2563eb",
    accent: "#d946ef",
    info: "#0284c7",
    success: "#059669",
    warning: "#d97706",
    error: "#dc2626",
  },
  nord: {
    isDark: false,
    base100: "#ffffff",
    base200: "#eceff4",
    base300: "#e5e9f0",
    baseContent: "#1e293b",
    baseBorder: "#2563eb",
    primary: "#2563eb",
    secondary: "#0284c7",
    accent: "#7c3aed",
    info: "#0284c7",
    success: "#16a34a",
    warning: "#d97706",
    error: "#dc2626",
  },
  corporate: {
    isDark: false,
    base100: "#ffffff",
    base200: "#f4f6f8",
    base300: "#e5e9ec",
    baseContent: "#0f172a",
    baseBorder: "#2563eb",
    primary: "#2563eb",
    secondary: "#475569",
    accent: "#0284c7",
    info: "#0284c7",
    success: "#16a34a",
    warning: "#d97706",
    error: "#dc2626",
  },
  light: {
    isDark: false,
    base100: "#ffffff",
    base200: "#f8fafc",
    base300: "#f1f5f9",
    baseContent: "#0f172a",
    baseBorder: "#4f46e5",
    primary: "#4f46e5",
    secondary: "#db2777",
    accent: "#0284c7",
    info: "#0284c7",
    success: "#16a34a",
    warning: "#d97706",
    error: "#dc2626",
  },
};

/**
 * Safely parse any CSS color (OKLCH, HSL, RGB, Hex, etc.) using Culori and format to standard #rrggbb Hex.
 */
export function toHexColor(colorStr: string | null | undefined, fallback: string): string {
  if (!colorStr) return fallback;
  const trimmed = colorStr.trim();
  try {
    const parsed = parse(trimmed);
    if (parsed) {
      const hex = formatHex(parsed);
      if (hex) return hex;
    }
  } catch {
    // Fall back if culori cannot parse
  }
  return fallback;
}

let probeElement: HTMLElement | null = null;

function getOrCreateProbe(): HTMLElement | null {
  if (typeof document === "undefined") return null;
  if (!probeElement || !document.body.contains(probeElement)) {
    let existing = document.getElementById("daisyui-mermaid-color-probe");
    if (!existing) {
      existing = document.createElement("div");
      existing.id = "daisyui-mermaid-color-probe";
      existing.setAttribute("aria-hidden", "true");
      existing.style.cssText =
        "position:fixed;top:-9999px;left:-9999px;width:0;height:0;opacity:0;pointer-events:none;overflow:hidden;z-index:-9999;";
      existing.innerHTML = `
        <div id="probe-base-100" class="bg-base-100 text-base-content border-base-300"></div>
        <div id="probe-base-200" class="bg-base-200 text-base-content border-base-300"></div>
        <div id="probe-base-300" class="bg-base-300 text-base-content border-base-content/20"></div>
        <div id="probe-primary" class="bg-primary text-primary-content border-primary"></div>
        <div id="probe-secondary" class="bg-secondary text-secondary-content border-secondary"></div>
        <div id="probe-accent" class="bg-accent text-accent-content border-accent"></div>
        <div id="probe-info" class="bg-info text-info-content border-info"></div>
        <div id="probe-success" class="bg-success text-success-content border-success"></div>
        <div id="probe-warning" class="bg-warning text-warning-content border-warning"></div>
        <div id="probe-error" class="bg-error text-error-content border-error"></div>
      `;
      document.body.appendChild(existing);
    }
    probeElement = existing;
  }
  return probeElement;
}

export function getDaisyUIThemeColors() {
  const currentThemeAttr =
    (typeof document !== "undefined" && document.documentElement.getAttribute("data-theme")) ||
    "business";
  const fallback = THEME_PALETTES[currentThemeAttr] || THEME_PALETTES["business"];

  if (typeof window === "undefined" || typeof document === "undefined") {
    return {
      ...fallback,
      piePalette: DEFAULT_VIBRANT_PALETTE,
    };
  }

  const knownTheme = THEMES.find((t) => t.id === currentThemeAttr);
  const isDark = knownTheme ? knownTheme.isDark : fallback.isDark;

  getOrCreateProbe();
  const elB1 = document.getElementById("probe-base-100");
  const elB2 = document.getElementById("probe-base-200");
  const elB3 = document.getElementById("probe-base-300");
  const elP = document.getElementById("probe-primary");
  const elS = document.getElementById("probe-secondary");
  const elA = document.getElementById("probe-accent");
  const elInfo = document.getElementById("probe-info");
  const elSucc = document.getElementById("probe-success");
  const elWarn = document.getElementById("probe-warning");
  const elErr = document.getElementById("probe-error");

  const rawBase100 = elB1 ? window.getComputedStyle(elB1).backgroundColor : null;
  const rawBase200 = elB2 ? window.getComputedStyle(elB2).backgroundColor : null;
  const rawBase300 = elB3 ? window.getComputedStyle(elB3).backgroundColor : null;
  const rawPrimary = elP ? window.getComputedStyle(elP).backgroundColor : null;
  const rawSecondary = elS ? window.getComputedStyle(elS).backgroundColor : null;
  const rawAccent = elA ? window.getComputedStyle(elA).backgroundColor : null;
  const rawInfo = elInfo ? window.getComputedStyle(elInfo).backgroundColor : null;
  const rawSuccess = elSucc ? window.getComputedStyle(elSucc).backgroundColor : null;
  const rawWarning = elWarn ? window.getComputedStyle(elWarn).backgroundColor : null;
  const rawError = elErr ? window.getComputedStyle(elErr).backgroundColor : null;

  const hexInfo = toHexColor(rawInfo, fallback.info);
  const hexSuccess = toHexColor(rawSuccess, fallback.success);
  const hexWarning = toHexColor(rawWarning, fallback.warning);
  const hexError = toHexColor(rawError, fallback.error);
  const hexAccent = toHexColor(rawAccent, fallback.accent);
  const hexSecondary = toHexColor(rawSecondary, fallback.secondary);
  const hexPrimary = toHexColor(rawPrimary, fallback.primary);

  // Dynamic semantic pie palette derived from theme semantic highlights
  const piePalette = [
    hexInfo, // 1: Info (Sky/Cyan)
    hexSuccess, // 2: Success (Green/Emerald)
    hexWarning, // 3: Warning (Amber/Gold)
    hexSecondary, // 4: Secondary (Violet/Indigo)
    hexError, // 5: Error (Rose/Red)
    hexAccent, // 6: Accent (Pink/Magenta)
    "#14b8a6", // 7: Teal
    "#f97316", // 8: Orange
    "#3b82f6", // 9: Blue
    "#84cc16", // 10: Lime
    "#d946ef", // 11: Fuchsia
    "#06b6d4", // 12: Cyan
  ];

  const parsedPrimary: Color | undefined =
    (rawPrimary && parse(rawPrimary)) || parse(fallback.primary) || undefined;
  const parsedBase100: Color | undefined =
    (rawBase100 && parse(rawBase100)) || parse(fallback.base100) || undefined;

  let mainBkg = fallback.base100;
  let nodeBorder = hexInfo || fallback.baseBorder;
  let lineColor = hexInfo || fallback.primary;
  let nodeTextColor = isDark ? "#f8fafc" : "#0f172a";
  const edgeLabelBkg = isDark ? "#0f172a" : "#ffffff";
  const clusterBkg = isDark ? "#131b28" : "#f1f5f9";
  const clusterBorder = isDark ? "#334155" : "#cbd5e1";

  if (isDark) {
    // Dark mode: Elevate node card background and use vibrant border (Info/Sky) for high visibility
    if (parsedBase100) {
      const bOklch = oklch(parsedBase100);
      if (bOklch) {
        const elevated = {
          ...bOklch,
          l: Math.max(0.24, Math.min(0.3, (bOklch.l || 0.18) + 0.08)),
          c: Math.max(0.015, bOklch.c || 0.015),
        };
        mainBkg = formatHex(elevated) || fallback.base100;
      }
    }

    if (parsedPrimary) {
      const pOklch = oklch(parsedPrimary);
      if (pOklch) {
        const vibrantLine = {
          ...pOklch,
          l: Math.max(0.72, Math.min(0.85, (pOklch.l || 0.5) * 1.5)),
          c: Math.max(0.14, pOklch.c || 0.14),
        };
        lineColor = formatHex(vibrantLine) || hexInfo || fallback.primary;
      }
    }
    // High-contrast node border using Info / Primary
    nodeBorder = hexInfo || hexPrimary || "#38bdf8";
  } else {
    // Light mode: Clean white cards with vivid borders and deep readable lines
    mainBkg = "#ffffff";
    nodeTextColor = "#0f172a";
    nodeBorder = hexInfo || hexPrimary || "#0284c7";

    if (parsedPrimary) {
      const pOklch = oklch(parsedPrimary);
      if (pOklch) {
        const highContrastLine = {
          ...pOklch,
          l: Math.min(0.42, Math.max(0.3, (pOklch.l || 0.6) * 0.7)),
          c: Math.max(0.14, pOklch.c || 0.14),
        };
        lineColor = formatHex(highContrastLine) || hexInfo || fallback.primary;
      }
    }
  }

  const base200 = toHexColor(rawBase200, fallback.base200);
  const base300 = toHexColor(rawBase300, fallback.base300);

  return {
    isDark,
    mainBkg,
    nodeBorder,
    nodeTextColor,
    lineColor,
    edgeLabelBkg,
    clusterBkg,
    clusterBorder,
    base100: mainBkg,
    base200,
    base300,
    baseContent: nodeTextColor,
    baseBorder: nodeBorder,
    primary: hexPrimary,
    secondary: hexSecondary,
    accent: hexAccent,
    info: hexInfo,
    success: hexSuccess,
    warning: hexWarning,
    error: hexError,
    piePalette,
  };
}

export function configureMermaidForTheme() {
  const colors = getDaisyUIThemeColors();
  const palette = colors.piePalette;

  mermaid.initialize({
    startOnLoad: false,
    htmlLabels: false,
    theme: "base",
    themeVariables: {
      darkMode: colors.isDark,
      background: "transparent",
      mainBkg: colors.mainBkg,
      nodeBorder: colors.nodeBorder,
      nodeTextColor: colors.nodeTextColor,
      textColor: colors.nodeTextColor,
      titleColor: colors.nodeTextColor,
      primaryColor: colors.mainBkg,
      primaryTextColor: colors.nodeTextColor,
      primaryBorderColor: colors.nodeBorder,
      lineColor: colors.lineColor,
      secondaryColor: colors.base200,
      secondaryTextColor: colors.nodeTextColor,
      secondaryBorderColor: colors.nodeBorder,
      tertiaryColor: colors.clusterBkg,
      tertiaryTextColor: colors.nodeTextColor,
      tertiaryBorderColor: colors.clusterBorder,
      edgeLabelBackground: colors.edgeLabelBkg,
      clusterBkg: colors.clusterBkg,
      clusterBorder: colors.clusterBorder,
      actorBkg: colors.mainBkg,
      actorBorder: colors.nodeBorder,
      actorTextColor: colors.nodeTextColor,
      actorLineColor: colors.nodeBorder,
      signalColor: colors.nodeTextColor,
      signalTextColor: colors.nodeTextColor,
      labelBoxBkgColor: colors.edgeLabelBkg,
      labelBoxBorderColor: colors.nodeBorder,
      labelTextColor: colors.nodeTextColor,
      loopTextColor: colors.nodeTextColor,
      noteBorderColor: colors.nodeBorder,
      noteBkgColor: colors.edgeLabelBkg,
      noteTextColor: colors.nodeTextColor,
      activationBorderColor: colors.lineColor,
      activationBkgColor: colors.base300,
      sequenceNumberColor: colors.isDark ? "#0f172a" : "#ffffff",

      // Pie Chart Theme Variables
      pie1: palette[0],
      pie2: palette[1],
      pie3: palette[2],
      pie4: palette[3],
      pie5: palette[4],
      pie6: palette[5],
      pie7: palette[6],
      pie8: palette[7],
      pie9: palette[8],
      pie10: palette[9],
      pie11: palette[10],
      pie12: palette[11],
      pieTitleTextColor: colors.nodeTextColor,
      pieTitleTextSize: "16px",
      pieSectionTextColor: "#ffffff",
      pieSectionTextSize: "13px",
      pieLegendTextColor: colors.nodeTextColor,
      pieLegendTextSize: "13px",
      pieStrokeColor: colors.isDark ? "#0f172a" : "#ffffff",
      pieStrokeWidth: "2px",
      pieOpacity: "0.95",

      // Semantic Color Scales & Class Definitions
      cScale0: palette[0],
      cScale1: palette[1],
      cScale2: palette[2],
      cScale3: palette[3],
      cScale4: palette[4],
      cScale5: palette[5],
      cScale6: palette[6],
      cScale7: palette[7],
      cScale8: palette[8],
      cScale9: palette[9],
      cScale10: palette[10],
      cScale11: palette[11],

      fillType0: palette[0],
      fillType1: palette[1],
      fillType2: palette[2],
      fillType3: palette[4], // error / rose
      fillType4: palette[3], // secondary / violet
      fillType5: palette[5], // accent / pink
      fillType6: palette[6], // teal
      fillType7: palette[7], // orange

      git0: palette[0],
      git1: palette[1],
      git2: palette[2],
      git3: palette[3],
      git4: palette[4],
      git5: palette[5],
      git6: palette[6],
      git7: palette[7],

      stateBkg: colors.mainBkg,
      stateLabelColor: colors.nodeTextColor,

      fontFamily:
        "Inter, system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
      fontSize: "13px",
    },
    flowchart: {
      htmlLabels: false,
      useMaxWidth: true,
      nodeSpacing: 50,
      rankSpacing: 65,
      padding: 20,
      curve: "basis",
    },
    pie: {
      useMaxWidth: true,
      textPosition: 0.65,
    },
    securityLevel: "loose",
  });
}
