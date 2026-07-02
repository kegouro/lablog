export interface DiffLine {
  kind: 'same' | 'add' | 'del'
  text: string
}

// ponytail: LCS por líneas con recorte de prefijo/sufijo común. Cubre documentos
// de bitácora; si el núcleo editado excede 1500×1500 líneas devuelve null y la
// UI muestra un aviso (upgrade path: diff de Myers).
export function diffLines(a: string, b: string): DiffLine[] | null {
  const A = a.split('\n')
  const B = b.split('\n')
  let pre = 0
  while (pre < A.length && pre < B.length && A[pre] === B[pre]) pre++
  let endA = A.length
  let endB = B.length
  while (endA > pre && endB > pre && A[endA - 1] === B[endB - 1]) {
    endA--
    endB--
  }
  const midA = A.slice(pre, endA)
  const midB = B.slice(pre, endB)
  if (midA.length * midB.length > 1500 * 1500) return null

  const n = midA.length
  const m = midB.length
  const dp: Uint16Array[] = Array.from({ length: n + 1 }, () => new Uint16Array(m + 1))
  for (let i = n - 1; i >= 0; i--) {
    for (let j = m - 1; j >= 0; j--) {
      dp[i][j] = midA[i] === midB[j] ? dp[i + 1][j + 1] + 1 : Math.max(dp[i + 1][j], dp[i][j + 1])
    }
  }

  const out: DiffLine[] = A.slice(0, pre).map((text) => ({ kind: 'same' as const, text }))
  let i = 0
  let j = 0
  while (i < n && j < m) {
    if (midA[i] === midB[j]) {
      out.push({ kind: 'same', text: midA[i] })
      i++
      j++
    } else if (dp[i + 1][j] >= dp[i][j + 1]) {
      out.push({ kind: 'del', text: midA[i] })
      i++
    } else {
      out.push({ kind: 'add', text: midB[j] })
      j++
    }
  }
  while (i < n) out.push({ kind: 'del', text: midA[i++] })
  while (j < m) out.push({ kind: 'add', text: midB[j++] })
  out.push(...A.slice(endA).map((text) => ({ kind: 'same' as const, text })))
  return out
}
