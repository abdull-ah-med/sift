"use client";

import { Viewer, Worker, type RenderPageProps } from "@react-pdf-viewer/core";
import "@react-pdf-viewer/core/lib/styles/index.css";
import { createContext, useContext, useEffect, useMemo } from "react";
import { bboxToOverlayStyle, type BBox } from "@/lib/bbox";

export type OverlayBlock = {
  id: string;
  page: number;
  bbox: BBox | null;
};

type Props = {
  fileUrl: string;
  overlays: OverlayBlock[];
  selectedBlockId?: string | null;
  onSelectBlock?: (blockId: string) => void;
};

const SelectedBlockContext = createContext<string | null>(null);

function PageWithOverlays({
  props,
  overlays,
  onSelectBlock,
}: {
  props: RenderPageProps;
  overlays: OverlayBlock[];
  onSelectBlock?: (blockId: string) => void;
}) {
  const pageNo = props.pageIndex + 1;
  const pageOverlays = overlays.filter((o) => o.page === pageNo && o.bbox);
  const selectedBlockId = useContext(SelectedBlockContext);

  useEffect(() => {
    if (props.canvasLayerRendered && props.textLayerRendered) {
      props.markRendered(props.pageIndex);
    }
  }, [
    props.canvasLayerRendered,
    props.textLayerRendered,
    props.markRendered,
    props.pageIndex,
  ]);

  // Overlay layer last so hit-targets sit above text/annotation (Phase 2 §4.4).
  return (
    <>
      {props.canvasLayer.children}
      {props.textLayer.children}
      {props.annotationLayer.children}
      <div
        className="rpv-overlay-layer"
        style={{
          position: "absolute",
          left: 0,
          top: 0,
          width: "100%",
          height: "100%",
          pointerEvents: "none",
        }}
      >
        {pageOverlays.map((o) => {
          if (!o.bbox) return null;
          const pageWidthPts = props.scale > 0 ? props.width / props.scale : props.width;
          const pageHeightPts = props.scale > 0 ? props.height / props.scale : props.height;
          const style = bboxToOverlayStyle(o.bbox, pageWidthPts, pageHeightPts);
          return (
            <button
              key={o.id}
              type="button"
              className={o.id === selectedBlockId ? "bbox-overlay selected" : "bbox-overlay"}
              style={{ ...style, pointerEvents: "auto" }}
              aria-label={`Block ${o.id}`}
              onClick={() => onSelectBlock?.(o.id)}
            />
          );
        })}
      </div>
    </>
  );
}

export default function ReviewPdfViewer({
  fileUrl,
  overlays,
  selectedBlockId = null,
  onSelectBlock,
}: Props) {
  // Geometry only — selection must not change renderPage identity (scroll/zoom).
  const geometry = useMemo(
    () => overlays.map(({ id, page, bbox }) => ({ id, page, bbox })),
    [overlays],
  );

  const renderPage = useMemo(
    () => (props: RenderPageProps) => (
      <PageWithOverlays props={props} overlays={geometry} onSelectBlock={onSelectBlock} />
    ),
    [geometry, onSelectBlock],
  );

  return (
    <SelectedBlockContext.Provider value={selectedBlockId}>
      <div className="review-pdf" aria-label="PDF viewer">
        <Worker workerUrl="/pdf.worker.min.js">
          <Viewer
            fileUrl={fileUrl}
            renderPage={renderPage}
            // Mitigate CVE-2024-4367 while pinned to pdfjs 3.x required by @react-pdf-viewer/core@3.12.
            transformGetDocumentParams={(params) => ({
              ...params,
              isEvalSupported: false,
            })}
          />
        </Worker>
      </div>
    </SelectedBlockContext.Provider>
  );
}
