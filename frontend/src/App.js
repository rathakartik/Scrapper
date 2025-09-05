import React, { useState, useEffect } from "react";
import "./App.css";
import axios from "axios";
import { Button } from "./components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./components/ui/card";
import { Badge } from "./components/ui/badge";
import { Input } from "./components/ui/input";
import { Label } from "./components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./components/ui/tabs";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "./components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "./components/ui/select";
import { Textarea } from "./components/ui/textarea";
import { Switch } from "./components/ui/switch";
import { toast } from "sonner";
import { Toaster } from "./components/ui/sonner";
import { RefreshCw, Download, Plus, Settings, TrendingUp, Building2, MapPin, Calendar, ExternalLink, Trash2, Edit } from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const App = () => {
  const [startups, setStartups] = useState([]);
  const [newsSources, setNewsSources] = useState([]);
  const [stats, setStats] = useState({});
  const [loading, setLoading] = useState(false);
  const [filters, setFilters] = useState({
    industry: '',
    location: '',
    funding_stage: ''
  });
  const [newSource, setNewSource] = useState({
    name: '',
    url: '',
    rss_feed: '',
    css_selectors: {}
  });
  const [showAddSource, setShowAddSource] = useState(false);
  const [scrapingLogs, setScrapingLogs] = useState([]);

  useEffect(() => {
    fetchStartups();
    fetchNewsSources();
    fetchStats();
    fetchScrapingLogs();
    
    // Auto-refresh every 2 minutes
    const interval = setInterval(() => {
      fetchStartups();
      fetchStats();
    }, 120000);
    
    return () => clearInterval(interval);
  }, []);

  const fetchStartups = async () => {
    try {
      const params = new URLSearchParams();
      if (filters.industry) params.append('industry', filters.industry);
      if (filters.location) params.append('location', filters.location);
      if (filters.funding_stage) params.append('funding_stage', filters.funding_stage);
      
      const response = await axios.get(`${API}/startups?${params}`);
      setStartups(response.data);
    } catch (error) {
      console.error('Error fetching startups:', error);
      toast.error('Failed to fetch startups');
    }
  };

  const fetchNewsSources = async () => {
    try {
      const response = await axios.get(`${API}/news-sources`);
      setNewsSources(response.data);
    } catch (error) {
      console.error('Error fetching news sources:', error);
    }
  };

  const fetchStats = async () => {
    try {
      const response = await axios.get(`${API}/startups/stats`);
      setStats(response.data);
    } catch (error) {
      console.error('Error fetching stats:', error);
    }
  };

  const fetchScrapingLogs = async () => {
    try {
      const response = await axios.get(`${API}/logs`);
      setScrapingLogs(response.data);
    } catch (error) {
      console.error('Error fetching logs:', error);
    }
  };

  const triggerManualScrape = async () => {
    setLoading(true);
    try {
      await axios.post(`${API}/scrape/trigger`);
      toast.success('Manual scraping triggered! Results will appear shortly.');
      setTimeout(() => {
        fetchStartups();
        fetchStats();
        fetchScrapingLogs();
      }, 10000);
    } catch (error) {
      console.error('Error triggering scrape:', error);
      toast.error('Failed to trigger scraping');
    } finally {
      setLoading(false);
    }
  };

  const exportCSV = async () => {
    try {
      const response = await axios.get(`${API}/export/csv`, {
        responseType: 'blob'
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'startups_funding_data.csv');
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      
      toast.success('CSV exported successfully!');
    } catch (error) {
      console.error('Error exporting CSV:', error);
      toast.error('Failed to export CSV');
    }
  };

  const addNewsSource = async () => {
    try {
      await axios.post(`${API}/news-sources`, newSource);
      setNewSource({ name: '', url: '', rss_feed: '', css_selectors: {} });
      setShowAddSource(false);
      fetchNewsSources();
      toast.success('News source added successfully!');
    } catch (error) {
      console.error('Error adding news source:', error);
      toast.error('Failed to add news source');
    }
  };

  const deleteNewsSource = async (sourceId) => {
    try {
      await axios.delete(`${API}/news-sources/${sourceId}`);
      fetchNewsSources();
      toast.success('News source deleted successfully!');
    } catch (error) {
      console.error('Error deleting news source:', error);
      toast.error('Failed to delete news source');
    }
  };

  const applyFilters = () => {
    fetchStartups();
  };

  const clearFilters = () => {
    setFilters({ industry: '', location: '', funding_stage: '' });
    setTimeout(fetchStartups, 100);
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-IN', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getFundingStageColor = (stage) => {
    const colors = {
      'seed': 'bg-green-100 text-green-800',
      'series a': 'bg-blue-100 text-blue-800',
      'series b': 'bg-purple-100 text-purple-800',
      'series c': 'bg-orange-100 text-orange-800',
      'pre-series a': 'bg-yellow-100 text-yellow-800'
    };
    return colors[stage?.toLowerCase()] || 'bg-gray-100 text-gray-800';
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100">
      <Toaster />
      
      {/* Header */}
      <div className="bg-white/80 backdrop-blur-sm border-b border-slate-200/60 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-gradient-to-br from-blue-600 to-purple-700 rounded-xl flex items-center justify-center">
                <TrendingUp className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold bg-gradient-to-r from-gray-900 via-blue-800 to-purple-800 bg-clip-text text-transparent">
                  Startup Funding Tracker
                </h1>
                <p className="text-sm text-slate-600">Real-time Indian startup funding intelligence</p>
              </div>
            </div>
            
            <div className="flex items-center space-x-3">
              <Button
                onClick={triggerManualScrape}
                disabled={loading}
                className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white shadow-lg hover:shadow-xl transition-all duration-200"
              >
                {loading ? (
                  <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                ) : (
                  <RefreshCw className="w-4 h-4 mr-2" />
                )}
                {loading ? 'Scraping...' : 'Scan Now'}
              </Button>
              
              <Button
                onClick={exportCSV}
                variant="outline"
                className="border-slate-300 hover:bg-slate-50 shadow-sm"
              >
                <Download className="w-4 h-4 mr-2" />
                Export CSV
              </Button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <Card className="bg-white/80 backdrop-blur-sm border-slate-200/60 shadow-lg hover:shadow-xl transition-shadow">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-slate-600">Total Startups</CardTitle>
              <Building2 className="w-4 h-4 text-blue-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-slate-900">{stats.total_startups || 0}</div>
            </CardContent>
          </Card>
          
          <Card className="bg-white/80 backdrop-blur-sm border-slate-200/60 shadow-lg hover:shadow-xl transition-shadow">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-slate-600">Recent Discoveries</CardTitle>
              <Calendar className="w-4 h-4 text-green-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-slate-900">{stats.recent_discoveries || 0}</div>
              <p className="text-xs text-slate-500">Last 24 hours</p>
            </CardContent>
          </Card>
          
          <Card className="bg-white/80 backdrop-blur-sm border-slate-200/60 shadow-lg hover:shadow-xl transition-shadow">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-slate-600">Active Sources</CardTitle>
              <Settings className="w-4 h-4 text-purple-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-slate-900">{newsSources.filter(s => s.is_active).length}</div>
            </CardContent>
          </Card>
          
          <Card className="bg-white/80 backdrop-blur-sm border-slate-200/60 shadow-lg hover:shadow-xl transition-shadow">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-slate-600">Top Industry</CardTitle>
              <TrendingUp className="w-4 h-4 text-orange-600" />
            </CardHeader>
            <CardContent>
              <div className="text-lg font-bold text-slate-900">
                {stats.top_industries?.[0]?._id || 'N/A'}
              </div>
              <p className="text-xs text-slate-500">
                {stats.top_industries?.[0]?.count || 0} startups
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Main Content */}
        <Tabs defaultValue="startups" className="space-y-6">
          <TabsList className="bg-white/80 backdrop-blur-sm border border-slate-200/60 shadow-sm">
            <TabsTrigger value="startups" className="data-[state=active]:bg-blue-100 data-[state=active]:text-blue-700">
              Discovered Startups
            </TabsTrigger>
            <TabsTrigger value="sources" className="data-[state=active]:bg-purple-100 data-[state=active]:text-purple-700">
              News Sources
            </TabsTrigger>
            <TabsTrigger value="logs" className="data-[state=active]:bg-green-100 data-[state=active]:text-green-700">
              Scraping Logs
            </TabsTrigger>
          </TabsList>

          {/* Startups Tab */}
          <TabsContent value="startups" className="space-y-6">
            {/* Filters */}
            <Card className="bg-white/80 backdrop-blur-sm border-slate-200/60 shadow-lg">
              <CardHeader>
                <CardTitle className="text-lg font-semibold text-slate-800">Filters</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                  <div>
                    <Label htmlFor="industry" className="text-sm font-medium text-slate-700">Industry</Label>
                    <Input
                      id="industry"
                      placeholder="e.g., Fintech, EdTech"
                      value={filters.industry}
                      onChange={(e) => setFilters({...filters, industry: e.target.value})}
                      className="mt-1 border-slate-300 focus:border-blue-500 focus:ring-blue-500"
                    />
                  </div>
                  <div>
                    <Label htmlFor="location" className="text-sm font-medium text-slate-700">Location</Label>
                    <Input
                      id="location"
                      placeholder="e.g., Bangalore, Mumbai"
                      value={filters.location}
                      onChange={(e) => setFilters({...filters, location: e.target.value})}
                      className="mt-1 border-slate-300 focus:border-blue-500 focus:ring-blue-500"
                    />
                  </div>
                  <div>
                    <Label htmlFor="funding_stage" className="text-sm font-medium text-slate-700">Funding Stage</Label>
                    <Input
                      id="funding_stage"
                      placeholder="e.g., Seed, Series A"
                      value={filters.funding_stage}
                      onChange={(e) => setFilters({...filters, funding_stage: e.target.value})}
                      className="mt-1 border-slate-300 focus:border-blue-500 focus:ring-blue-500"
                    />
                  </div>
                  <div className="flex items-end space-x-2">
                    <Button onClick={applyFilters} className="bg-blue-600 hover:bg-blue-700 text-white flex-1">
                      Apply Filters
                    </Button>
                    <Button onClick={clearFilters} variant="outline" className="border-slate-300">
                      Clear
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Startups List */}
            <div className="grid gap-6">
              {startups.length === 0 ? (
                <Card className="bg-white/80 backdrop-blur-sm border-slate-200/60 shadow-lg">
                  <CardContent className="flex flex-col items-center justify-center py-16">
                    <Building2 className="w-16 h-16 text-slate-400 mb-4" />
                    <h3 className="text-lg font-semibold text-slate-600 mb-2">No startups found</h3>
                    <p className="text-slate-500 text-center max-w-md">
                      Try adjusting your filters or trigger a manual scan to discover new funding announcements.
                    </p>
                  </CardContent>
                </Card>
              ) : (
                startups.map((startup) => (
                  <Card key={startup.id} className="bg-white/80 backdrop-blur-sm border-slate-200/60 shadow-lg hover:shadow-xl transition-all duration-200">
                    <CardHeader>
                      <div className="flex justify-between items-start">
                        <div>
                          <CardTitle className="text-xl font-bold text-slate-900 mb-2">
                            {startup.name}
                          </CardTitle>
                          <div className="flex flex-wrap gap-2 mb-3">
                            {startup.funding_stage && (
                              <Badge className={`${getFundingStageColor(startup.funding_stage)} border-0`}>
                                {startup.funding_stage}
                              </Badge>
                            )}
                            {startup.funding_amount && (
                              <Badge variant="outline" className="border-green-300 text-green-700 bg-green-50">
                                {startup.funding_amount}
                              </Badge>
                            )}
                            {startup.industry && (
                              <Badge variant="outline" className="border-blue-300 text-blue-700 bg-blue-50">
                                {startup.industry}
                              </Badge>
                            )}
                          </div>
                        </div>
                        <div className="text-right text-sm text-slate-500">
                          <p className="flex items-center">
                            <Calendar className="w-4 h-4 mr-1" />
                            {formatDate(startup.discovered_at)}
                          </p>
                        </div>
                      </div>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      {startup.location && (
                        <div className="flex items-center text-slate-600">
                          <MapPin className="w-4 h-4 mr-2 text-slate-500" />
                          <span>{startup.location}</span>
                        </div>
                      )}
                      
                      {startup.investors && startup.investors.length > 0 && (
                        <div>
                          <h4 className="text-sm font-semibold text-slate-700 mb-2">Investors</h4>
                          <div className="flex flex-wrap gap-2">
                            {startup.investors.map((investor, idx) => (
                              <Badge key={idx} variant="secondary" className="bg-slate-100 text-slate-700">
                                {investor}
                              </Badge>
                            ))}
                          </div>
                        </div>
                      )}
                      
                      <div className="flex flex-wrap gap-3 pt-3 border-t border-slate-200">
                        {startup.website && (
                          <a
                            href={startup.website}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center text-sm text-blue-600 hover:text-blue-800 hover:underline"
                          >
                            <ExternalLink className="w-3 h-3 mr-1" />
                            Website
                          </a>
                        )}
                        {startup.linkedin_profile && (
                          <a
                            href={startup.linkedin_profile}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center text-sm text-blue-600 hover:text-blue-800 hover:underline"
                          >
                            <ExternalLink className="w-3 h-3 mr-1" />
                            LinkedIn
                          </a>
                        )}
                        {startup.source_url && (
                          <a
                            href={startup.source_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center text-sm text-slate-500 hover:text-slate-700 hover:underline"
                          >
                            <ExternalLink className="w-3 h-3 mr-1" />
                            Source
                          </a>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                ))
              )}
            </div>
          </TabsContent>

          {/* News Sources Tab */}
          <TabsContent value="sources" className="space-y-6">
            <div className="flex justify-between items-center">
              <h2 className="text-2xl font-bold text-slate-800">News Sources Management</h2>
              <Dialog open={showAddSource} onOpenChange={setShowAddSource}>
                <DialogTrigger asChild>
                  <Button className="bg-gradient-to-r from-green-600 to-blue-600 hover:from-green-700 hover:to-blue-700 text-white">
                    <Plus className="w-4 h-4 mr-2" />
                    Add Source
                  </Button>
                </DialogTrigger>
                <DialogContent className="sm:max-w-[525px]">
                  <DialogHeader>
                    <DialogTitle>Add News Source</DialogTitle>
                    <DialogDescription>
                      Add a new news source to monitor for startup funding announcements.
                    </DialogDescription>
                  </DialogHeader>
                  <div className="grid gap-4 py-4">
                    <div>
                      <Label htmlFor="name">Source Name</Label>
                      <Input
                        id="name"
                        value={newSource.name}
                        onChange={(e) => setNewSource({...newSource, name: e.target.value})}
                        placeholder="e.g., TechCrunch India"
                      />
                    </div>
                    <div>
                      <Label htmlFor="url">Website URL</Label>
                      <Input
                        id="url"
                        value={newSource.url}
                        onChange={(e) => setNewSource({...newSource, url: e.target.value})}
                        placeholder="https://example.com"
                      />
                    </div>
                    <div>
                      <Label htmlFor="rss">RSS Feed URL (Optional)</Label>
                      <Input
                        id="rss"
                        value={newSource.rss_feed}
                        onChange={(e) => setNewSource({...newSource, rss_feed: e.target.value})}
                        placeholder="https://example.com/feed.xml"
                      />
                    </div>
                  </div>
                  <DialogFooter>
                    <Button onClick={addNewsSource} className="bg-blue-600 hover:bg-blue-700 text-white">
                      Add Source
                    </Button>
                  </DialogFooter>
                </DialogContent>
              </Dialog>
            </div>

            <div className="grid gap-4">
              {newsSources.map((source) => (
                <Card key={source.id} className="bg-white/80 backdrop-blur-sm border-slate-200/60 shadow-lg">
                  <CardHeader>
                    <div className="flex justify-between items-start">
                      <div>
                        <CardTitle className="text-lg font-semibold text-slate-800">{source.name}</CardTitle>
                        <CardDescription className="mt-1">
                          <a href={source.url} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">
                            {source.url}
                          </a>
                        </CardDescription>
                      </div>
                      <div className="flex items-center space-x-2">
                        <Badge variant={source.is_active ? "default" : "secondary"}>
                          {source.is_active ? "Active" : "Inactive"}
                        </Badge>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => deleteNewsSource(source.id)}
                          className="text-red-600 hover:text-red-800 hover:bg-red-50"
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </div>
                    </div>
                  </CardHeader>
                  {source.rss_feed && (
                    <CardContent>
                      <div className="text-sm text-slate-600">
                        <strong>RSS Feed:</strong> {source.rss_feed}
                      </div>
                    </CardContent>
                  )}
                </Card>
              ))}
            </div>
          </TabsContent>

          {/* Scraping Logs Tab */}
          <TabsContent value="logs" className="space-y-6">
            <h2 className="text-2xl font-bold text-slate-800">Scraping Activity Logs</h2>
            
            <div className="grid gap-4">
              {scrapingLogs.length === 0 ? (
                <Card className="bg-white/80 backdrop-blur-sm border-slate-200/60 shadow-lg">
                  <CardContent className="flex flex-col items-center justify-center py-16">
                    <Settings className="w-16 h-16 text-slate-400 mb-4" />
                    <h3 className="text-lg font-semibold text-slate-600 mb-2">No logs available</h3>
                    <p className="text-slate-500">Scraping logs will appear here once the system starts running.</p>
                  </CardContent>
                </Card>
              ) : (
                scrapingLogs.map((log) => (
                  <Card key={log.id} className="bg-white/80 backdrop-blur-sm border-slate-200/60 shadow-lg">
                    <CardContent className="pt-6">
                      <div className="flex justify-between items-start">
                        <div>
                          <div className="flex items-center space-x-3 mb-2">
                            <Badge 
                              variant={log.status === 'success' ? 'default' : 'destructive'}
                              className={log.status === 'success' ? 'bg-green-100 text-green-800' : ''}
                            >
                              {log.status}
                            </Badge>
                            <span className="text-sm text-slate-600">
                              Source ID: {log.source_id.substring(0, 8)}...
                            </span>
                          </div>
                          <div className="grid grid-cols-2 gap-4 text-sm">
                            <div>
                              <span className="text-slate-500">Articles Processed:</span>
                              <span className="ml-2 font-semibold text-slate-700">{log.articles_processed}</span>
                            </div>
                            <div>
                              <span className="text-slate-500">Startups Found:</span>
                              <span className="ml-2 font-semibold text-slate-700">{log.startups_found}</span>
                            </div>
                          </div>
                          {log.error_message && (
                            <div className="mt-2 text-sm text-red-600 bg-red-50 p-2 rounded">
                              {log.error_message}
                            </div>
                          )}
                        </div>
                        <div className="text-right text-sm text-slate-500">
                          {formatDate(log.timestamp)}
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))
              )}
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};

export default App;