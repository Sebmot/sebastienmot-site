window.sortSitePosts = function sortSitePosts(posts) {
  const pinned = posts.filter((p) => p.pinned).sort((a, b) => b.date.localeCompare(a.date));
  const rest = posts.filter((p) => !p.pinned).sort((a, b) => b.date.localeCompare(a.date));
  return [...pinned, ...rest];
};
