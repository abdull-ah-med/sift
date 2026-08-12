/**
 * Convert sift provenance bbox (PDF bottom-left origin points) to CSS overlay %.
 */
export type BBox = { x0: number; y0: number; x1: number; y1: number };

export type OverlayStyle = {
  left: string;
  top: string;
  width: string;
  height: string;
};

export function bboxToOverlayStyle(
  bbox: BBox,
  pageWidth: number,
  pageHeight: number,
): OverlayStyle {
  if (pageWidth <= 0 || pageHeight <= 0) {
    return { left: "0%", top: "0%", width: "0%", height: "0%" };
  }
  const x0 = Math.min(bbox.x0, bbox.x1);
  const x1 = Math.max(bbox.x0, bbox.x1);
  const y0 = Math.min(bbox.y0, bbox.y1);
  const y1 = Math.max(bbox.y0, bbox.y1);
  const left = (x0 / pageWidth) * 100;
  const width = ((x1 - x0) / pageWidth) * 100;
  const top = ((pageHeight - y1) / pageHeight) * 100;
  const height = ((y1 - y0) / pageHeight) * 100;
  return {
    left: `${left}%`,
    top: `${top}%`,
    width: `${width}%`,
    height: `${height}%`,
  };
}
