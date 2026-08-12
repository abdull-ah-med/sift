"use client";

import * as CollapsiblePrimitive from "@radix-ui/react-collapsible";

export function Collapsible(props: React.ComponentProps<typeof CollapsiblePrimitive.Root>) {
  return <CollapsiblePrimitive.Root {...props} />;
}

export function CollapsibleTrigger(
  props: React.ComponentProps<typeof CollapsiblePrimitive.CollapsibleTrigger>,
) {
  return <CollapsiblePrimitive.CollapsibleTrigger {...props} />;
}

export function CollapsibleContent(
  props: React.ComponentProps<typeof CollapsiblePrimitive.CollapsibleContent>,
) {
  return <CollapsiblePrimitive.CollapsibleContent {...props} />;
}
