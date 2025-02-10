import { styled, Tooltip } from '@mui/material';
import Tab from '@mui/material/Tab';
import Tabs from '@mui/material/Tabs';
import * as React from 'react';

interface TabPanelProps {
  children?: React.ReactNode;
  dir?: string;
  index: number;
  value: number;
}

export function PublicTabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      className="h-[calc(100vh-100px)]"
      {...other}
    >
      {value === index && children}
    </div>
  );
}

export function PrivateTabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      className="h-[calc(100vh-100px)] bg-neutral-200"
      style={{ borderRadius: '16px' }}
      {...other}
    >
      {value === index && (
        <>
          {children}
          <div
            style={{
              position: 'absolute',
              right: '50px',
              bottom: '30px',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              opacity: 0.8,
            }}
          >
            <Tooltip
              title="This workspace component is visible only to you. AI teammates can't see your actions here."
              arrow
              placement="left"
            >
              <img
                src="/incognito.svg"
                alt="Incognito"
                style={{
                  width: '36px',
                  height: '36px',
                  cursor: 'pointer',
                }}
              />
            </Tooltip>
          </div>
        </>
      )}
    </div>
  );
}

export const CustomTab = styled(Tab)({
  textTransform: 'none',
  minWidth: 72,
  fontWeight: 500,
  padding: '0px 20px',
  borderRadius: '9999px',
  '&.Mui-selected': {
    backgroundColor: '#edf5ff',
    color: '#479cff',
  },
  '&:hover': {
    backgroundColor: '#f2f2f2',
  },
});

export const CustomTabs = styled(Tabs)({
  display: 'inline-flex',
  borderBottom: 'none',
  '& .MuiTabs-indicator': {
    display: 'none',
  },
  marginBottom: '15px',
  backgroundColor: '#f2f2f2',
  borderRadius: '9999px',
});

export const TabWithNotification: React.FC<{ label: string; hasUpdate: boolean }> = ({
  label,
  hasUpdate,
}) => (
  <div className="relative">
    {label}
    {hasUpdate && <div className="absolute -top-1 -right-1 w-2 h-2 rounded-full bg-blue-500" />}
  </div>
);
