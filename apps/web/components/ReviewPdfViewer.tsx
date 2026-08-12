"use client";

import { Viewer, Worker, type RenderPageProps } from "@react-pdf-viewer/core";
import "@react-pdf-viewer/core/lib/styles/index.css";
import { useEffect, useMemo } from "react";
import { bboxToOverlayStyle, type BBox } from "@/lib/bbox";

export type OverlayBlock = {
  id: string;
  page: number;
  bbox: BBox | null;
  selected: boolean;
};

type Props = {
  fileUrl: string;
  overlays: OverlayBlock[];
  onSelectBlock?: (blockId: string) => void;
};

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

  return (
    <>
      {props.canvasLayer.children}
      <div className="rpv-overlay-layer" style={{ width: "100%", height: "100%", position: "relative" }}>
        {pageOverlays.map((o) => {
          if (!o.bbox) return null;
          const pageWidthPts = props.scale > 0 ? props.width / props.scale : props.width;
          const pageHeightPts = props.scale > 0 ? props.height / props.scale : props.height;
          const style = bboxToOverlayStyle(o.bbox, pageWidthPts, pageHeightPts);
          return (
            <button
              key={o.id}
              type="button"
              className={o.selected ? "bbox-overlay selected" : "bbox-overlay"}
              style={style}
              aria-label={`Block ${o.id}`}
              onClick={() => onSelectBlock?.(o.id)}
            />
          );
        })}
      </div>
      {props.textLayer.children}
      {props.annotationLayer.children}
    </>
  );
}

export default function ReviewPdfViewer({ fileUrl, overlays, onSelectBlock }: Props) {
  const renderPage = useMemo(
    () => (props: RenderPageProps) => (
      <PageWithOverlays props={props} overlays={overlays} onSelectBlock={onSelectBlock} />
    ),
    [overlays, onSelectBlock],
  );

  return (
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
  );
}
