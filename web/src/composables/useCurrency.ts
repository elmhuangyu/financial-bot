import { ref } from "vue";

export type Currency = "USD" | "CAD";

const currentCurrency = ref<Currency>("USD");
const fxRateUsdCad = ref<number>(1.3767);

export function useCurrency() {
  function setCurrency(curr: Currency) {
    currentCurrency.value = curr;
  }

  function setFxRate(rate: number) {
    fxRateUsdCad.value = rate;
  }

  function formatMoney(amount: number | string | undefined | null, isPrivacy = false): string {
    if (isPrivacy) return "••••••";
    const num =
      typeof amount === "number" ? amount : parseFloat(String(amount || 0).replace(/,/g, ""));
    if (isNaN(num)) return "$0.00";

    const converted = currentCurrency.value === "CAD" ? num * fxRateUsdCad.value : num;
    const prefix = currentCurrency.value === "CAD" ? "C$" : "$";

    return (
      prefix +
      converted.toLocaleString("en-US", {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      })
    );
  }

  return {
    currentCurrency,
    fxRateUsdCad,
    setCurrency,
    setFxRate,
    formatMoney,
  };
}
