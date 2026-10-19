import React from 'react';
import { Layout } from '../components/common/Layout';
import { AddLinkForm } from '../components/links/AddLinkForm';
import { LinkList } from '../components/links/LinkList';
import { SearchBar } from '../components/search/SearchBar';
import { TagFilter } from '../components/search/TagFilter';
import { useLinks } from '../hooks/useLinks';

export const DashboardPage: React.FC = () => {
  const {
    links,
    isLoading,
    searchQuery,
    setSearchQuery,
    selectedTag,
    setSelectedTag,
    availableTags,
    addLink,
    updateLink,
    deleteLink,
    downloadVideo,
    clearFilters,
    isFiltered,
  } = useLinks();

  return (
    <Layout>
      {/* Link Submission */}
      <AddLinkForm onAddLink={addLink} />

      {/* Exploration Controls: Search & Tags */}
      <div className="mb-6 space-y-3">
        <div className="flex flex-col sm:flex-row gap-3">
          <SearchBar
            value={searchQuery}
            onChange={setSearchQuery}
            onClear={() => setSearchQuery('')}
          />
        </div>

        <TagFilter
          availableTags={availableTags}
          selectedTag={selectedTag}
          onSelectTag={setSelectedTag}
        />
      </div>

      {/* Links Grid */}
      <LinkList
        links={links}
        isLoading={isLoading}
        onDelete={deleteLink}
        onUpdate={updateLink}
        onDownload={downloadVideo}
        onSelectTag={setSelectedTag}
        onClearFilters={clearFilters}
        isFiltered={isFiltered}
      />
    </Layout>
  );
};
