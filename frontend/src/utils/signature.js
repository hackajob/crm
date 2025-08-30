// Make hrefs absolute/safe
export function normalizeHref(href) {
  if (!href) return ''
  const s = href.trim()
  if (/^(javascript|vbscript):/i.test(s)) return ''
  if (/^data:(?!image\/)/i.test(s)) return ''
  if (/^(https?:|ftp:|mailto:|tel:|cid:)/i.test(s)) return s
  if (s.startsWith('//')) return `https:${s}`
  if (s.startsWith('/')) {
    try { return new URL(s, window.location.origin).href } catch { return s }
  }
  if (s.startsWith('#')) return s
  return `https://${s.replace(/^https?:\/\//i, '')}`
}

export function hasSignature(html) {
  return /data-signature="true"|\bclass=["'][^"']*signature[^"']*["']/i.test(html || '')
}

// Clean signature HTML (unwrap .ql-editor, absolutize links/imgs, remove stray <br>)
export function buildCleanSignature(raw) {
  if (!raw) return ''
  const html = String(raw).replace(/\n/g, '<br>')
  try {
    const doc = new DOMParser().parseFromString(html, 'text/html')
    const ql = doc.querySelector('.ql-editor')
    const container = document.createElement('div')
    container.innerHTML = ql ? ql.innerHTML : doc.body.innerHTML

    // Unwrap invalid p>div nesting from Quill exports
    container.innerHTML = container.innerHTML.replace(
      /<p[^>]*>\s*<div[^>]*>([\s\S]*?)<\/div>\s*<\/p>/gi,
      '$1'
    )

    // Absolutize images
    const imgNodes = []
    container.querySelectorAll('img').forEach((img) => {
      const src = img.getAttribute('src') || ''
      const isAbs = /^(?:[a-z]+:)?\/\//i.test(src) || src.startsWith('data:') || src.startsWith('cid:')
      const absolute = isAbs ? src : new URL(src, window.location.origin).href
      if (absolute !== src) img.setAttribute('src', absolute)
      imgNodes.push({
        src: absolute,
        alt: img.getAttribute('alt') || null,
        title: img.getAttribute('title') || null,
        width: img.getAttribute('width') || null,
        height: img.getAttribute('height') || null,
        style: img.getAttribute('style') || null,
        class: img.getAttribute('class') || null,
      })
    })

    // Normalize links
    container.querySelectorAll('a').forEach((a) => {
      const href = a.getAttribute('href') || ''
      const normalized = normalizeHref(href)
      if (normalized) a.setAttribute('href', normalized)
      a.setAttribute('target', '_blank')
      const rel = new Set((a.getAttribute('rel') || '').split(/\s+/).filter(Boolean))
      rel.add('noopener'); rel.add('noreferrer')
      a.setAttribute('rel', Array.from(rel).join(' '))
    })

    // Remove stray <br>:
    // - Keep <p></p> for true blank lines
    // - Remove <br> inside non-empty <p>
    // - Remove <br> outside <p>
    container.querySelectorAll('p').forEach((p) => {
      const nodes = Array.from(p.childNodes).filter(
        (n) => !(n.nodeType === Node.TEXT_NODE && !n.textContent.trim())
      )
      const hasNonBr = nodes.some((n) => n.nodeName !== 'BR')
      if (!hasNonBr) {
        p.innerHTML = ''
      } else {
        p.querySelectorAll('br').forEach((br) => br.remove())
      }
    })
    container.querySelectorAll('br').forEach((br) => {
      if (!br.closest('p')) br.remove()
    })

    // Defensive: normalize <p><br></p> → <p></p>
    const cleaned = container.innerHTML.replace(/<p>\s*<br\s*\/?>\s*<\/p>/gi, '<p></p>')
    return {html:`<div class="signature" data-signature="true">${cleaned}</div>`, imgNodes}
  } catch {
    return {html:`<div class="signature" data-signature="true">${html}</div>`, imgNodes: imgNodes ?? []}
  }
}

export function trimTrailingEmptyParas(html) {
  return (html || '').replace(/(?:\s*<p>\s*<\/p>\s*)+$/gi, '')
}

// Append signature to base HTML with exactly two blank lines before it
export function appendSignatureToHTML(base, userSigRaw) {
  const twoBlank = '<p></p><p></p>'
  const cleanedBase = trimTrailingEmptyParas(base || '')
  const sig = buildCleanSignature(userSigRaw)
  return {html:`${cleanedBase}${twoBlank}${sig.html}`, imgNodes: sig.imgNodes}
}