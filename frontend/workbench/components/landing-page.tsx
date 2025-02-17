'use client';

import { handleStartSession } from '@/lib/start-session';
import { cn } from '@/lib/utils';
import MenuIcon from '@mui/icons-material/Menu';
import AppBar from '@mui/material/AppBar';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Container from '@mui/material/Container';
import IconButton from '@mui/material/IconButton';
import Menu from '@mui/material/Menu';
import MenuItem from '@mui/material/MenuItem';
import Paper from '@mui/material/Paper';
import Toolbar from '@mui/material/Toolbar';
import Typography from '@mui/material/Typography';
import { Paperclip, X } from 'lucide-react';
import { useRouter } from 'next/navigation';
import * as React from 'react';
import { useState } from 'react';
import toast from './toast';

const pages = ['Travel Planning', 'Literature Survey', 'Tabular Analysis'];

function ResponsiveAppBar({
  selectedTab,
  onTabChange,
}: {
  selectedTab: string;
  onTabChange: (tab: string) => void;
}) {
  const [anchorElNav, setAnchorElNav] = useState<null | HTMLElement>(null);

  const handleOpenNavMenu = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorElNav(event.currentTarget);
  };

  const handleCloseNavMenu = () => {
    setAnchorElNav(null);
  };

  return (
    <AppBar position="static" elevation={0} sx={{ backgroundColor: 'white', color: 'black' }}>
      <Container maxWidth="xl">
        <Toolbar disableGutters>
          <Typography
            variant="h6"
            noWrap
            component="a"
            sx={{
              mr: 2,
              display: { xs: 'none', md: 'flex' },
              fontFamily: 'monospace',
              fontWeight: 700,
              letterSpacing: '.3rem',
              color: 'black',
              textDecoration: 'none',
            }}
          >
            Collaborative Gym
          </Typography>
          <Box sx={{ flexGrow: 1, display: { xs: 'flex', md: 'none' } }}>
            <IconButton
              size="large"
              aria-label="account of current user"
              aria-controls="menu-appbar"
              aria-haspopup="true"
              onClick={handleOpenNavMenu}
              color="inherit"
            >
              <MenuIcon />
            </IconButton>
            <Menu
              id="menu-appbar"
              anchorEl={anchorElNav}
              anchorOrigin={{ vertical: 'bottom', horizontal: 'left' }}
              keepMounted
              transformOrigin={{ vertical: 'top', horizontal: 'left' }}
              open={Boolean(anchorElNav)}
              onClose={handleCloseNavMenu}
              sx={{ display: { xs: 'block', md: 'none' } }}
            >
              {pages.map((page) => (
                <MenuItem
                  key={page}
                  onClick={() => {
                    onTabChange(page);
                    handleCloseNavMenu();
                  }}
                  sx={{
                    fontWeight: selectedTab === page ? 700 : 400,
                    fontSize: '16px',
                  }}
                >
                  <Typography sx={{ textAlign: 'center' }}>{page}</Typography>
                </MenuItem>
              ))}
            </Menu>
          </Box>
          <Typography
            variant="h5"
            noWrap
            component="a"
            sx={{
              mr: 2,
              display: { xs: 'flex', md: 'none' },
              flexGrow: 1,
              fontFamily: 'monospace',
              fontWeight: 700,
              letterSpacing: '.3rem',
              color: 'black',
              textDecoration: 'none',
            }}
          >
            Collaborative Gym
          </Typography>
          <Box sx={{ flexGrow: 1, display: { xs: 'none', md: 'flex' } }}>
            {pages.map((page) => (
              <Button
                key={page}
                onClick={() => onTabChange(page)}
                sx={{
                  my: 2,
                  pt: 1,
                  color: 'black',
                  display: 'block',
                  textTransform: 'none',
                  fontWeight: selectedTab === page ? 700 : 400,
                  fontSize: '16px',
                }}
              >
                {page}
              </Button>
            ))}
          </Box>
        </Toolbar>
      </Container>
    </AppBar>
  );
}

function MainContent({ selectedTab }: { selectedTab: string }) {
  const router = useRouter();
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [TravelPlanningInitialQuery, setTravelPlanningInitialQuery] = useState<string>('');
  const [LitSurveyInitialQuery, setLitSurveyInitialQuery] = useState<string>('');
  const [TabularAnalysisQuery, setTabularAnalysisQuery] = useState<string>('');
  const [attachedFiles, setAttachedFiles] = useState<File[]>([]);

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const newFiles = Array.from(event.target.files || []) as File[];
    const updatedFiles = [...attachedFiles, ...newFiles];
    // Remove duplicates based on file name
    const uniqueFiles = updatedFiles.filter(
      (file, index, self) =>
        index === self.findIndex((f) => f.name === file.name)
    );
    setAttachedFiles(uniqueFiles);
  };

  const handleDeleteFile = (fileToDelete: File) => {
    const newFileList = new DataTransfer();
    Array.from(attachedFiles).forEach(file => {
      if (file !== fileToDelete) {
        newFileList.items.add(file);
      }
    });
    setAttachedFiles(Array.from(newFileList.files));
  };

  const handleStart = async () => {
    if (submitting) return;
    setSubmitting(true);
    const formData = new FormData();

    console.log('Starting session with selected tab:', selectedTab);

    if (selectedTab === 'Travel Planning') {
      if (!TravelPlanningInitialQuery.trim()) {
        toast.error('start-session', 'Please describe where you want to go and your requirements.');
        setSubmitting(false);
        return;
      }
      formData.append('task', 'travel_planning');
      formData.append('query', TravelPlanningInitialQuery);
    } else if (selectedTab === 'Literature Survey') {
      if (!LitSurveyInitialQuery.trim()) {
        toast.error('start-session', 'Please describe your initial query.');
        setSubmitting(false);
        return;
      }
      formData.append('task', 'lit_survey');
      formData.append('query', LitSurveyInitialQuery);
    } else if (selectedTab === 'Tabular Analysis') {
      if (!TabularAnalysisQuery.trim()) {
        toast.error('start-session', 'Please describe how you want to analyze your data.');
        setSubmitting(false);
        return;
      }
      if (attachedFiles.length === 0) {
        toast.error('start-session', 'Please attach at least one CSV file.');
        setSubmitting(false);
        return;
      }
      formData.append('task', 'tabular_analysis');
      formData.append('query', TabularAnalysisQuery);
      attachedFiles.forEach((file) => formData.append('tables', file));
    }

    try {
      const { sessionId, task } = await handleStartSession(formData, 'local-user');
      toast.success('start-session', 'Session started successfully!');
      router.push(`/session/${sessionId}?task=${task}`);
    } catch (error) {
      console.error('Failed to start session:', error);
      toast.error('start-session', 'Could not start the session. Please try again.');
    }
    setSubmitting(false);
  };

  const predefinedTabularanalysisData = [
    {
      query: 'Examine the impact of COVID-19 on the United States and summarize the findings.',
      tables: ['covid19_weekly_deaths_the_united_states.csv'],
    },
    {
      query:
        "Analyze the impact of COVID-19 on birth rates. Consider the effects of various variables that may influence birth rates. Additionally, assess correlations between birth outcomes and the incidence of COVID-19 among pregnant women using available data.\nSummarize the findings into a short report.",
      tables: ['covid19-birth-statistics.csv', 'women-with-covid-during-pregnancy.csv'],
    },
    {
      query: 'Explore insights from the US presidential election data.',
      tables: ['2024_us_presidential_results.csv'],
    },
    {
      query:
        "Perform a comparative analysis of the 2024 US presidential election results in the context of historical trends from 1976 to 2020.\nSummarize the findings into a short report.",
      tables: ['2024_us_presidential_results.csv', '1976-2020-president.csv'],
    },
    {
      query:
        "Conduct a comprehensive analysis of global climate change data by examining long-term trends in annual surface temperature changes and atmospheric CO2 concentrations. Explore feedback loops if possible.\nSummarize the findings into a short report.",
      tables: ['Annual_Surface_Temperature_Change.csv', 'Atmospheric_CO2_Concentrations.csv'],
    },
  ];

  const exampleTableDir = 'example-tables/';

  const setPredefinedTabularAnalysisData = async () => {
    const randomIndex = Math.floor(Math.random() * predefinedTabularanalysisData.length);
    setTabularAnalysisQuery(predefinedTabularanalysisData[randomIndex].query);

    const files = await Promise.all(
      predefinedTabularanalysisData[randomIndex].tables.map(async (table) => {
        const response = await fetch(`${exampleTableDir}${table}`);
        const data = await response.blob();
        return new File([data], table);
      })
    );
    setAttachedFiles(files);
  };

  return (
    <Box display="flex" p={4} alignItems="center" justifyContent="center">
      <Box width="40%" mr={4} alignItems="flex-start">
        <Typography variant="h4" sx={{ fontWeight: 'bold', mb: 2 }}>
          {selectedTab === 'Travel Planning' ? (
            <>
              <Box component="span" sx={{ color: 'primary.main' }}>
                Plan your trip
              </Box>
              {' together with AI agent'}
            </>
          ) : selectedTab === 'Literature Survey' ? (
            <>
              <Box component="span" sx={{ color: 'primary.main' }}>
                Write Related Work section
              </Box>
              {' together with AI agent'}
            </>
          ) : (
            <>
              <Box component="span" sx={{ color: 'primary.main' }}>
                Analyze your tabular data
              </Box>
              {' together with AI agent'}
            </>
          )}
        </Typography>
        <Box display="flex" flexDirection="column" gap={2}>
          {selectedTab === 'Travel Planning' && (
            <textarea
              value={TravelPlanningInitialQuery}
              onChange={(e) => setTravelPlanningInitialQuery(e.target.value)}
              placeholder="Describe where you want to go and your requirements..."
              style={{ minHeight: '200px', fontFamily: 'monospace', fontSize: '16px' }}
              className={cn(
                'block w-full h-full resize-none bg-gray-100 p-4 rounded-md focus:outline-none focus:ring-0 border-none font-mono'
              )}
            />
          )}
          {selectedTab === 'Literature Survey' && (
            <textarea
              value={LitSurveyInitialQuery}
              onChange={(e) => setLitSurveyInitialQuery(e.target.value)}
              placeholder="Describe what topic you want to write about and your requirements..."
              style={{ minHeight: '200px', fontFamily: 'monospace', fontSize: '16px' }}
              className={cn(
                'block w-full h-full resize-none bg-gray-100 p-4 rounded-md focus:outline-none focus:ring-0 border-none font-mono'
              )}
            />
          )}
          {selectedTab === 'Tabular Analysis' && (
            <Box sx={{ flexDirection: 'column', backgroundColor: 'grey.100' }}>
              <textarea
                value={TabularAnalysisQuery}
                onChange={(e) => setTabularAnalysisQuery(e.target.value)}
                placeholder="Attach the CSV file and describe how you want to analyze your data..."
                style={{ minHeight: '200px', fontFamily: 'monospace', fontSize: '16px' }}
                className={cn(
                  "block w-full min-h-[200px] resize-none bg-gray-100 p-4",
                  "rounded-md focus:outline-none focus:ring-0 border-none font-mono text-base"
                )}
              />
              {/* File attachment */}
              <div className="flex flex-col mt-4">
                <Box display="flex" alignItems="center" ml={1} mb={1}>
                  <button
                    style={{
                      position: 'relative',
                      right: 0,
                      background: 'none',
                      border: 'none',
                      cursor: 'pointer',
                      transition: 'transform 0.2s, opacity 0.2s',
                    }}
                    onMouseOver={(e) => {
                      e.currentTarget.style.transform = 'scale(1.1)';
                      e.currentTarget.style.opacity = '0.8';
                    }}
                    onMouseOut={(e) => {
                      e.currentTarget.style.transform = 'scale(1)';
                      e.currentTarget.style.opacity = '1';
                    }}
                  >
                    <label className="cursor-pointer">
                      <Paperclip className="text-gray-600" />
                      <input
                        type="file"
                        hidden
                        multiple
                        onChange={handleFileChange}
                        accept=".csv,.xlsx,.xls"
                      />
                    </label>
                  </button>
                  {attachedFiles.length > 0 && (
                    <Typography variant="body2" sx={{ ml: 2, color: 'green' }}>
                      {attachedFiles.length} file(s) attached
                    </Typography>
                  )}
                  {attachedFiles.length === 0 && (
                    <Typography variant="body2" sx={{ ml: 2, color: 'gray' }}>
                      Please attach at least one CSV file
                    </Typography>
                  )}
                </Box>
                {/* File list with delete buttons */}
                {attachedFiles.length > 0 && (
                  <div className="h-16 overflow-x-auto overflow-y-hidden mx-2 mb-1">
                    <div className="flex flex-row gap-2 h-full py-2">
                      {Array.from(attachedFiles).map((file, index) => (
                        <div
                          key={`${file.name}-${index}`}
                          className="flex items-center bg-white px-3 rounded-md whitespace-nowrap shadow-sm"
                        >
                          <span className="text-sm text-gray-700 max-w-[200px] truncate">
                            {file.name}
                          </span>
                          <button
                            onClick={() => handleDeleteFile(file)}
                            className="p-1 hover:bg-gray-100 rounded-full transition-colors flex-shrink-0"
                            aria-label={`Delete ${file.name}`}
                          >
                            <X className="w-4 h-4 text-gray-500" />
                          </button>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </Box>
          )}
          <Box display="flex" justifyContent="flex-start" gap={2}>
            <Button
              variant="contained"
              sx={{ backgroundColor: 'black', color: 'white', mt: 2, alignSelf: 'flex-start' }}
              onClick={handleStart}
              disabled={submitting}
            >
              Let's start!
            </Button>
            {selectedTab === 'Tabular Analysis' && (
              <Button
                variant="outlined"
                sx={{ mt: 2, alignSelf: 'flex-start' }}
                onClick={setPredefinedTabularAnalysisData}
              >
                Explore example query
              </Button>
            )}
          </Box>
        </Box>
      </Box>
      <Paper
        elevation={0}
        sx={{
          width: '38%',
          aspectRatio: '1 / 1',
          backgroundColor: 'white',
          backgroundImage: `url(/cogym-logo.svg)`,
          backgroundSize: 'cover',
          backgroundPosition: 'center',
          ml: 4,
        }}
      />
    </Box>
  );
}

export default function LandingPage() {
  const [selectedTab, setSelectedTab] = React.useState<string>(pages[0]);

  return (
    <Box>
      <ResponsiveAppBar selectedTab={selectedTab} onTabChange={setSelectedTab} />
      <Box mt={4}>
        <MainContent selectedTab={selectedTab} />
      </Box>
    </Box>
  );
}
