import * as React from 'react';

import { DynamicLayout } from '@/components/dashboard/layout/dynamic-layout';

interface LayoutProps {
  children: React.ReactNode;
}

export default function Layout({ children }: LayoutProps): React.JSX.Element {
  return <DynamicLayout>{children}</DynamicLayout>;
}
