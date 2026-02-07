/**
 * useAnnounceフック
 *
 * プログラムからスクリーンリーダーに通知を送るためのフック
 */

/**
 * スクリーンリーダー用アナウンスフック
 */
export function useAnnounce() {
  const announce = (message: string, politeness: "polite" | "assertive" = "polite") => {
    // 既存のライブリージョンにメッセージを設定
    const existingRegion = document.querySelector(
      `[aria-live="${politeness}"][role="status"], [aria-live="${politeness}"][role="alert"]`
    );

    if (existingRegion) {
      existingRegion.textContent = message;
    }
  };

  return { announce };
}
