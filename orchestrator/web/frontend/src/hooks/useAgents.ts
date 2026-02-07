/**
 * エージェントフック
 *
 * エージェント情報の取得と管理を提供します
 */

/**
 * アクティブなエージェントの統計を取得するフック
 * TODO: teamStore からの取得を無効化（無限ループ回避のため一時的に固定値）
 */
export function useAgentStats() {
  // TODO: teamStore を使わずに、選択されたチームのメンバーから計算する
  return {
    total: 0,
    running: 0,
    idle: 0,
    stopped: 0,
    error: 0,
  };
}
