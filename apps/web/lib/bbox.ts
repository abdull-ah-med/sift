/**
 * Convert sift provenance bbox (PDF bottom-left origin points) to CSS overlay %.
 * TDD stub — real math lands in the impl commit.
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
  void bbox;
  void pageWidth;
  void pageHeight;
  return { left: "0%", top: "0%", width: "0%", height: "0%" };
}
