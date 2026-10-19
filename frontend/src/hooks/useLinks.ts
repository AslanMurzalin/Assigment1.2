import { useState, useEffect, useCallback, useMemo } from 'react';
import type { CreateLinkInput, ILinkService, Link, UpdateLinkInput } from '../types';
import { mockLinkService } from '../api/services/mockLinkService';

export const useLinks = (linkService: ILinkService = mockLinkService) => {
  const [links, setLinks] = useState<Link[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [selectedTag, setSelectedTag] = useState<string | null>(null);

  const fetchLinks = useCallback(async () => {
    setIsLoading(true);
    try {
      const data = await linkService.getLinks({
        q: searchQuery,
        tag: selectedTag || undefined,
      });
      setLinks(data);
    } catch (err) {
      console.error('Failed to load links:', err);
    } finally {
      setIsLoading(false);
    }
  }, [linkService, searchQuery, selectedTag]);

  useEffect(() => {
    fetchLinks();
  }, [fetchLinks]);

  const addLink = async (input: CreateLinkInput) => {
    const created = await linkService.createLink(input);
    await fetchLinks();
    return created;
  };

  const updateLink = async (id: string, input: UpdateLinkInput) => {
    const updated = await linkService.updateLink(id, input);
    await fetchLinks();
    return updated;
  };

  const deleteLink = async (id: string) => {
    await linkService.deleteLink(id);
    await fetchLinks();
  };

  const downloadVideo = async (id: string) => {
    return await linkService.downloadVideo(id);
  };

  // Derive unique list of all tags currently in links
  const availableTags = useMemo(() => {
    const tagSet = new Set<string>();
    links.forEach((l) => l.tags.forEach((t) => tagSet.add(t)));
    return Array.from(tagSet).sort();
  }, [links]);

  const clearFilters = () => {
    setSearchQuery('');
    setSelectedTag(null);
  };

  const isFiltered = !!searchQuery || !!selectedTag;

  return {
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
    refetch: fetchLinks,
  };
};
