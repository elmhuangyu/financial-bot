/**
 * Resolves a high-contrast, visually appealing badge class based on the text value and column configuration.
 */
export function resolveBadgeClass(val: string, col?: any): string {
  if (!val) return "badge-tag-slate";

  const rawStr = String(val).trim();

  // If column has an explicit badgeColorMap matching raw or stripped text, use it
  if (col?.badgeColorMap) {
    if (col.badgeColorMap[rawStr]) return col.badgeColorMap[rawStr];
    if (col.badgeColorMap[rawStr.toUpperCase()]) return col.badgeColorMap[rawStr.toUpperCase()];
  }

  const clean = rawStr.toUpperCase();

  // 1. Financial Ratings & Grades
  if (clean === "A+" || clean === "AAA") return "badge-tag-emerald font-bold";
  if (clean === "A" || clean === "AA") return "badge-tag-emerald font-bold";
  if (clean === "A-" || clean === "BBB") return "badge-tag-teal font-semibold";
  if (clean.startsWith("B+") || clean === "B" || clean === "BB")
    return "badge-tag-amber font-semibold";
  if (clean.startsWith("B-") || clean.startsWith("C")) return "badge-tag-amber font-semibold";
  if (clean.startsWith("D") || clean.startsWith("F")) return "badge-tag-rose font-bold";

  // 2. Tax Regimes / Accounts
  if (
    clean.includes("TFSA") ||
    clean.includes("TAX-FREE") ||
    clean === "FREE" ||
    clean.includes("ROTH")
  ) {
    return "badge-tag-emerald font-semibold";
  }
  if (
    clean.includes("RRSP") ||
    clean.includes("TAX-DEFERRED") ||
    clean === "DEFERRED" ||
    clean.includes("401K") ||
    clean.includes("IRA") ||
    clean.includes("PENSION")
  ) {
    return "badge-tag-sky font-semibold";
  }
  if (clean.includes("TAXABLE") || clean.includes("NON-REG") || clean.includes("MARGIN")) {
    return "badge-tag-amber font-semibold";
  }
  if (clean.includes("MASTER") || clean.includes("ADVISOR")) {
    return "badge-tag-purple font-semibold";
  }

  // 3. Asset Classes
  if (
    clean.includes("US EQUIT") ||
    clean.includes("U.S. EQUIT") ||
    clean.includes("US STOCK") ||
    clean === "EQUITY" ||
    clean === "EQUITIES"
  ) {
    return "badge-tag-emerald font-semibold";
  }
  if (
    clean.includes("INTL") ||
    clean.includes("INTERNATIONAL") ||
    clean.includes("GLOBAL") ||
    clean.includes("EMERGING") ||
    clean.includes("DEVELOPED")
  ) {
    return "badge-tag-cyan font-semibold";
  }
  if (clean.includes("CANADIAN") || clean.includes("CANADA") || clean.includes("TSX")) {
    return "badge-tag-rose font-semibold";
  }
  if (
    clean.includes("DIGITAL") ||
    clean.includes("CRYPTO") ||
    clean.includes("BITCOIN") ||
    clean.includes("BTC") ||
    clean.includes("ETH")
  ) {
    return "badge-tag-purple font-semibold";
  }
  if (
    clean.includes("CASH") ||
    clean.includes("LIQUIDITY") ||
    clean.includes("MONEY MARKET") ||
    clean.includes("SAVINGS")
  ) {
    return "badge-tag-amber font-semibold";
  }
  if (
    clean.includes("FIXED INCOME") ||
    clean.includes("BOND") ||
    clean.includes("TREASUR") ||
    clean.includes("DEBT")
  ) {
    return "badge-tag-indigo font-semibold";
  }
  if (clean.includes("REAL ESTATE") || clean.includes("REIT")) {
    return "badge-tag-orange font-semibold";
  }
  if (clean.includes("COMMODIT") || clean.includes("GOLD") || clean.includes("OIL")) {
    return "badge-tag-yellow font-semibold";
  }

  // 4. Status / Action / Direction
  if (
    clean.includes("BUY") ||
    clean.includes("OVERWEIGHT") ||
    clean.includes("PASS") ||
    clean.includes("OPTIMAL") ||
    clean.includes("SUCCESS")
  ) {
    return "badge-tag-emerald font-semibold";
  }
  if (clean.includes("HOLD") || clean.includes("NEUTRAL") || clean.includes("BALANCED")) {
    return "badge-tag-sky font-semibold";
  }
  if (
    clean.includes("SELL") ||
    clean.includes("UNDERWEIGHT") ||
    clean.includes("WARN") ||
    clean.includes("CAUTION")
  ) {
    return "badge-tag-amber font-semibold";
  }
  if (
    clean.includes("CRITICAL") ||
    clean.includes("FAIL") ||
    clean.includes("DANGER") ||
    clean.includes("HIGH RISK")
  ) {
    return "badge-tag-rose font-semibold";
  }

  // 5. Default Fallback (high contrast slate badge)
  return "badge-tag-slate font-medium";
}
