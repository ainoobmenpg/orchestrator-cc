/**
 * ConnectionStatusコンポーネント
 *
 * WebSocket接続状態を表示します
 * Framer Motionを使用して接続状態に応じたアニメーションを実装しています
 */

import { motion } from "framer-motion";
import { Wifi, WifiOff, Loader2 } from "lucide-react";
import type { ConnectionState } from "../../services/websocket";
import { cn } from "../../lib/utils";

interface ConnectionStatusProps {
  state: ConnectionState;
  className?: string;
}

export function ConnectionStatus({ state, className }: ConnectionStatusProps) {
  const config = {
    connected: {
      icon: Wifi,
      color: "text-green-500",
      bgColor: "bg-green-500/10",
      text: "接続中",
      animate: "pulse" as const,
    },
    connecting: {
      icon: Loader2,
      color: "text-yellow-500",
      bgColor: "bg-yellow-500/10",
      text: "接続中...",
      animate: "spin" as const,
    },
    disconnected: {
      icon: WifiOff,
      color: "text-red-500",
      bgColor: "bg-red-500/10",
      text: "切断中",
      animate: "blink" as const,
    },
    error: {
      icon: WifiOff,
      color: "text-red-500",
      bgColor: "bg-red-500/10",
      text: "エラー",
      animate: "blink" as const,
    },
  }[state];

  const Icon = config.icon;

  // ARIAラベル用の状態テキスト
  const ariaLabel = {
    connected: "接続中",
    connecting: "接続中",
    disconnected: "切断中",
    error: "エラー",
  }[state];

  // アニメーション定義
  const getAnimation = () => {
    switch (config.animate) {
      case "pulse":
        return {
          scale: [1, 1.1, 1],
          opacity: [1, 0.8, 1],
          transition: {
            duration: 1.5,
            repeat: Infinity,
            ease: "easeInOut" as const,
          },
        };
      case "spin":
        return {
          rotate: 360,
          transition: {
            duration: 1,
            repeat: Infinity,
            ease: "linear" as const,
          },
        };
      case "blink":
        return {
          opacity: [1, 0.3, 1],
          transition: {
            duration: 1,
            repeat: Infinity,
            ease: "easeInOut" as const,
          },
        };
      default:
        return {};
    }
  };

  return (
    <div
      role="status"
      aria-live="polite"
      aria-label={`接続状態: ${ariaLabel}`}
      className={cn(
        "flex items-center gap-2 rounded-md px-3 py-1.5 text-sm",
        config.bgColor,
        className,
      )}
    >
      <motion.div
        animate={getAnimation()}
        aria-hidden="true"
      >
        <Icon className={cn("h-4 w-4", config.color)} />
      </motion.div>
      <span className={config.color}>{config.text}</span>
    </div>
  );
}
