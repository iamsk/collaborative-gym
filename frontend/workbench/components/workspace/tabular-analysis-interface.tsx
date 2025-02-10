import {
    CustomTab,
    CustomTabs,
    PublicTabPanel,
    TabWithNotification,
  } from '@/components/tabs';
  import Box from '@mui/material/Box';
  import isEqual from 'lodash/isEqual';
  import * as React from 'react';
  import { useEffect, useRef, useState } from 'react';
  import JupyterEditor, { JupyterCellPair } from '../tools/jupyter-notebook/jupyter';
  import TextEditor from '../tools/text-editor';
  import CsvViewer, { CsvFile } from '../tools/csv-viewer';
  
  export interface TabularAnalysisWorkspaceInterfaceProps {
    textEditorContent: string;
    jupyterCells: JupyterCellPair[];
    csvFiles: CsvFile[];
    textEditorUpdateTrigger: number;
  }
  
  export default function TabularAnalysisWorkspaceInterface({
    textEditorContent,
    jupyterCells,
    csvFiles,
    textEditorUpdateTrigger,
  }: TabularAnalysisWorkspaceInterfaceProps) {
    const [value, setValue] = useState(0);
    const lastViewedContent = useRef({
      editor: textEditorContent,
      jupyter: jupyterCells,
    });
    const isInitialized = useRef(false);
  
    useEffect(() => {
      if (!isInitialized.current) {
        lastViewedContent.current = {
          editor: textEditorContent,
          jupyter: jupyterCells,
        };
        isInitialized.current = true;
      }
    }, [textEditorContent, jupyterCells]);
  
    const shouldShowNotification = (tabIndex: number) => {
      if (value === tabIndex) {
        switch (tabIndex) {
          case 0:
            lastViewedContent.current.editor = textEditorContent;
            break;
          case 1:
            lastViewedContent.current.jupyter = jupyterCells;
            break;
        }
        return false;
      }
      if (!isInitialized.current) return false;
      switch (tabIndex) {
        case 0:
          return !isEqual(lastViewedContent.current.editor, textEditorContent);
        case 1:
          return !isEqual(lastViewedContent.current.jupyter, jupyterCells);
        default:
          return false;
      }
    };
  
    const handleChange = (event: React.SyntheticEvent, newValue: number) => {
      setValue(newValue);
    };
  
    return (
      <Box sx={{ width: '95%', margin: '0 auto' }}>
        <Box
          sx={{
            width: '100%',
            display: 'flex',
            justifyContent: 'center',
          }}
        >
          <CustomTabs value={value} onChange={handleChange} centered>
            <CustomTab
              label={<TabWithNotification label="Editor" hasUpdate={shouldShowNotification(0)} />}
            />
            <CustomTab label={<TabWithNotification label="CSV Viewer" hasUpdate={false} />} />
            <CustomTab
              label={
                <TabWithNotification label="Jupyter Notebook" hasUpdate={shouldShowNotification(1)} />
              }
            />
          </CustomTabs>
        </Box>
        <PublicTabPanel value={value} index={0}>
          <TextEditor
            content={textEditorContent}
            textEditorUpdateTrigger={textEditorUpdateTrigger}
          />
        </PublicTabPanel>
        <PublicTabPanel value={value} index={1}>
          <CsvViewer files={csvFiles} />
        </PublicTabPanel>
        <PublicTabPanel value={value} index={2}>
          <JupyterEditor jupyterCells={jupyterCells} />
        </PublicTabPanel>
      </Box>
    );
  }
  