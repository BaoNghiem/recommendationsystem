/**
 * fixTitle — Chuẩn hóa tiêu đề phim từ định dạng MovieLens:
 *   "Godfather, The (1972)"   → "The Godfather (1972)"
 *   "Wrong Trousers, The"     → "The Wrong Trousers"
 *   "Bug's Life, A (1998)"    → "A Bug's Life (1998)"
 *
 * Hỗ trợ mạo từ: The, A, An (case-insensitive)
 *
 * @param {string} raw — tiêu đề gốc từ DB/dataset
 * @returns {string}   — tiêu đề đã chuẩn hóa
 */
export function fixTitle(raw) {
  if (!raw) return '';
  const match = raw.match(/^(.+),\s*(The|A|An)\s*(\((\d{4})\))?\s*$/i);
  if (match) {
    const name    = match[1].trim();
    const article = match[2];
    const yearPart = match[3] || '';
    return `${article} ${name} ${yearPart}`.trim();
  }
  return raw;
}

/**
 * splitTitle — Tách tiêu đề thành phần tên và năm:
 *   "The Godfather (1972)" → { name: "The Godfather", year: "1972" }
 *   "Toy Story (1995)"     → { name: "Toy Story", year: "1995" }
 *   "Alien"                → { name: "Alien", year: "" }
 *
 * @param {string} raw — tiêu đề gốc (chưa hoặc đã fix)
 * @returns {{ name: string, year: string }}
 */
export function splitTitle(raw) {
  const fixed = fixTitle(raw);
  const match = fixed.match(/^(.+?)\s*\((\d{4})\)\s*$/);
  if (match) return { name: match[1].trim(), year: match[2] };
  return { name: fixed, year: '' };
}

/**
 * getPosterUrl — Trả về URL ảnh poster phim.
 * Ưu tiên poster_url thật từ DB, fallback về SVG placeholder nội tuyến.
 *
 * @param {object} movie — object phim có thể chứa poster_url, title
 * @returns {string} — URL ảnh poster
 */
const BACKEND_URL = 'http://localhost:8000';
export function getPosterUrl(movie) {
  if (movie?.poster_url) {
    if (movie.poster_url.startsWith('http')) return movie.poster_url;
    return `${BACKEND_URL}${movie.poster_url}`;
  }
  
  // Use inline SVG for offline reliability
  const title = fixTitle(movie?.title || 'Movie');
  const shortTitle = title.length > 25 ? title.substring(0, 22) + '...' : title;
  
  // Create an SVG data URI
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="300" height="450" viewBox="0 0 300 450">
    <rect width="300" height="450" fill="#1a1a2e" />
    <rect width="300" height="450" fill="url(#grad)" />
    <defs>
      <linearGradient id="grad" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" style="stop-color:#2a2a4e;stop-opacity:1" />
        <stop offset="100%" style="stop-color:#1a1a2e;stop-opacity:1" />
      </linearGradient>
    </defs>
    <text x="50%" y="50%" dominant-baseline="middle" text-anchor="middle" fill="#8888aa" font-family="sans-serif" font-size="18" font-weight="bold" padding="20">
      ${shortTitle}
    </text>
    <text x="50%" y="60%" dominant-baseline="middle" text-anchor="middle" fill="#555577" font-family="sans-serif" font-size="14">
      No Poster
    </text>
  </svg>`;
  
  return `data:image/svg+xml;charset=utf-8,${encodeURIComponent(svg)}`;
}
