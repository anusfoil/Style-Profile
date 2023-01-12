

meta_attributes = compute_all_attributes(rerun=True)

labels = meta_attributes['artist'].unique()
attribute_by_label = meta_attributes.groupby('artist').mean()

X_axis = np.arange(len(labels))
plt.bar(X_axis - 0.4, attribute_by_label["sp_async_delta"], 0.4, label = 'avg_delta')
plt.bar(X_axis, attribute_by_label["sp_async_cor_onset"], 0.4, label = 'avg_cor_onset')
plt.bar(X_axis + 0.4, attribute_by_label["sp_async_cor_vel"], 0.4, label = 'avg_cor_vel')

plt.xticks(X_axis, labels, rotation = 45)
plt.legend()
plt.grid()
plt.show()
pass
