import {
    CustomTab,
    CustomTabs,
    PrivateTabPanel,
    PublicTabPanel,
    TabWithNotification,
  } from '@/components/tabs';
  import Box from '@mui/material/Box';
  import isEqual from 'lodash/isEqual';
  import * as React from 'react';
  import { useEffect, useRef, useState } from 'react';
  import PaperLibrary, { PaperLibraryItemProps } from '../tools/paper-library/paper-library';
  import PaperSearchInterface from '../tools/paper-search/paper-search-interface';
  import { PaperCardProps } from '../tools/paper-search/paper-search-result';
  import TextEditor from '../tools/text-editor';
  
  export interface RelatedWorksWorkspaceInterfaceProps {
    textEditorContent: string;
    paperLibraryContent: PaperLibraryItemProps[];
    paperSearchQuery: string;
    paperSearchResults: PaperCardProps[];
    textEditorUpdateTrigger: number;
  }
  
  export default function RelatedWorksWorkspaceInterface({
    textEditorContent,
    paperLibraryContent,
    paperSearchQuery,
    paperSearchResults,
    textEditorUpdateTrigger,
  }: RelatedWorksWorkspaceInterfaceProps) {
    const [value, setValue] = useState(0);
    const [lastViewed, setLastViewed] = useState({
      editor: Date.now(),
      library: Date.now(),
      search: Date.now(),
    });
  
    const lastViewedContent = useRef({
      editor: textEditorContent,
      library: paperLibraryContent,
      search: { query: paperSearchQuery, results: paperSearchResults },
    });
  
    const isInitialized = useRef(false);
  
    useEffect(() => {
      if (!isInitialized.current) {
        lastViewedContent.current = {
          editor: textEditorContent,
          library: paperLibraryContent,
          search: { query: paperSearchQuery, results: paperSearchResults },
        };
        isInitialized.current = true;
      }
    }, [textEditorContent, paperLibraryContent, paperSearchQuery, paperSearchResults]);
  
    const shouldShowNotification = (tabIndex: number) => {
      if (value === tabIndex) {
        switch (tabIndex) {
          case 0:
            lastViewedContent.current.editor = textEditorContent;
            break;
          case 1:
            lastViewedContent.current.library = paperLibraryContent;
            break;
          case 2:
            lastViewedContent.current.search = {
              query: paperSearchQuery,
              results: paperSearchResults,
            };
            break;
        }
        return false;
      }
  
      if (!isInitialized.current) return false;
  
      switch (tabIndex) {
        case 0:
          return !isEqual(lastViewedContent.current.editor, textEditorContent);
        case 1:
          return !isEqual(lastViewedContent.current.library, paperLibraryContent);
        case 2:
          return (
            !isEqual(lastViewedContent.current.search.query, paperSearchQuery) ||
            !isEqual(lastViewedContent.current.search.results, paperSearchResults)
          );
        default:
          return false;
      }
    };
  
    const handleChange = (event: React.SyntheticEvent, newValue: number) => {
      setValue(newValue);
      const now = Date.now();
      setLastViewed((prev) => ({
        ...prev,
        [newValue === 0 ? 'editor' : newValue === 1 ? 'library' : 'search']: now,
      }));
  
      if (newValue === 0) {
        lastViewedContent.current.editor = textEditorContent;
      } else if (newValue === 1) {
        lastViewedContent.current.library = paperLibraryContent;
      } else if (newValue === 2) {
        lastViewedContent.current.search = {
          query: paperSearchQuery,
          results: paperSearchResults,
        };
      }
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
            <CustomTab
              label={<TabWithNotification label="Library" hasUpdate={shouldShowNotification(1)} />}
            />
            <CustomTab
              label={<TabWithNotification label="Search" hasUpdate={shouldShowNotification(2)} />}
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
          <PaperLibrary papers={paperLibraryContent} />
        </PublicTabPanel>
        <PrivateTabPanel value={value} index={2}>
          <PaperSearchInterface query={paperSearchQuery} results={paperSearchResults} />
        </PrivateTabPanel>
      </Box>
    );
  }
  