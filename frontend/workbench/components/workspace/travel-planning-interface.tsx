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
  import DistanceMatrix, { DistanceMatrixResults } from '../tools/distance-matrix';
  import TextEditor from '../tools/text-editor';
  import TravelSearchInterface from '../tools/travel-search/travel-search-interface';
  import { TravelSearchResultCardProps } from '../tools/travel-search/travel-search-result';
  import { TravelSearchInputProps } from '../tools/travel-search/travel-search-input';
  
  export interface TravelPlanningWorkspaceInterfaceProps {
    textEditorContent: string;
    travelSearchInput: TravelSearchInputProps;
    travelSearchResults: TravelSearchResultCardProps[];
    distanceMatrixResults: DistanceMatrixResults | null;
    textEditorUpdateTrigger: number;
  }
  
  export default function TravelPlanningWorkspaceInterface({
    textEditorContent,
    travelSearchInput,
    travelSearchResults,
    distanceMatrixResults,
    textEditorUpdateTrigger,
  }: TravelPlanningWorkspaceInterfaceProps) {
    const [value, setValue] = useState(0);
    const lastViewedContent = useRef({
      editor: textEditorContent,
      search: { input: travelSearchInput, results: travelSearchResults },
      distanceMatrix: distanceMatrixResults,
    });
    const isInitialized = useRef(false);
  
    useEffect(() => {
      if (!isInitialized.current) {
        lastViewedContent.current = {
          editor: textEditorContent,
          search: { input: travelSearchInput, results: travelSearchResults },
          distanceMatrix: distanceMatrixResults,
        };
        isInitialized.current = true;
      }
    }, [textEditorContent, travelSearchInput, travelSearchResults, distanceMatrixResults]);
  
    const shouldShowNotification = (tabIndex: number) => {
      if (value === tabIndex) {
        switch (tabIndex) {
          case 0:
            lastViewedContent.current.editor = textEditorContent;
            break;
          case 1:
            lastViewedContent.current.search = { input: travelSearchInput, results: travelSearchResults };
            break;
          case 2:
            lastViewedContent.current.distanceMatrix = distanceMatrixResults;
            break;
        }
        return false;
      }
      if (!isInitialized.current) return false;
      switch (tabIndex) {
        case 0:
          return !isEqual(lastViewedContent.current.editor, textEditorContent);
        case 1:
          return (
            !isEqual(lastViewedContent.current.search.input, travelSearchInput) ||
            !isEqual(lastViewedContent.current.search.results, travelSearchResults)
          );
        case 2:
          return !isEqual(lastViewedContent.current.distanceMatrix, distanceMatrixResults);
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
            <CustomTab
              label={<TabWithNotification label="Search" hasUpdate={shouldShowNotification(1)} />}
            />
            <CustomTab
              label={
                <TabWithNotification label="Map" hasUpdate={shouldShowNotification(2)} />
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
        <PrivateTabPanel value={value} index={1}>
          <TravelSearchInterface input={travelSearchInput} results={travelSearchResults} />
        </PrivateTabPanel>
        <PrivateTabPanel value={value} index={2}>
          <DistanceMatrix currentResults={distanceMatrixResults} />
        </PrivateTabPanel>
      </Box>
    );
  }
  