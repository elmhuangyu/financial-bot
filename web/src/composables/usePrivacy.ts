import { ref } from "vue";

const isPrivacyMode = ref<boolean>(false);

export function usePrivacy() {
  function togglePrivacy() {
    isPrivacyMode.value = !isPrivacyMode.value;
  }

  function maskNumber(val: any, isPrivacy = isPrivacyMode.value): string {
    if (isPrivacy) return "•••";
    return String(val);
  }

  return {
    isPrivacyMode,
    togglePrivacy,
    maskNumber,
  };
}
