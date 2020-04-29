import os.path as osp
import shutil
import progressbar

import torch
from torch_geometric.data import InMemoryDataset, extract_zip
from torch_geometric.io import read_ply

class FAUSTRemeshed(InMemoryDataset):
    r"""The remeshed FAUST humans dataset from the paper `Multi-directional
    Geodesic Neural Networks via Equivariant Convolution`
    containing 100 watertight meshes representing 10 different poses for 10
    different subjects.

    .. note::

        Data objects hold mesh faces instead of edge indices.
        To convert the mesh to a graph, use the
        :obj:`torch_geometric.transforms.FaceToEdge` as :obj:`pre_transform`.
        To convert the mesh to a point cloud, use the
        :obj:`torch_geometric.transforms.SamplePoints` as :obj:`transform` to
        sample a fixed number of points on the mesh faces according to their
        face area.

    Args:
        root (string): Root directory where the dataset should be saved.
        train (bool, optional): If :obj:`True`, loads the training dataset,
            otherwise the test dataset. (default: :obj:`True`)
        transform (callable, optional): A function/transform that takes in an
            :obj:`torch_geometric.data.Data` object and returns a transformed
            version. The data object will be transformed before every access.
            (default: :obj:`None`)
        pre_transform (callable, optional): A function/transform that takes in
            an :obj:`torch_geometric.data.Data` object and returns a
            transformed version. The data object will be transformed before
            being saved to disk. (default: :obj:`None`)
        pre_filter (callable, optional): A function that takes in an
            :obj:`torch_geometric.data.Data` object and returns a boolean
            value, indicating whether the data object should be included in the
            final dataset. (default: :obj:`None`)
    """

    url = 'https://github.com/rubenwiersma/hsn'

    def __init__(self, root, train=True, transform=None, pre_transform=None,
                 pre_filter=None):
        super(FAUSTRemeshed, self).__init__(root, transform, pre_transform, pre_filter)
        path = self.processed_paths[0] if train else self.processed_paths[-1]
        self.data, self.slices = torch.load(path)

    @property
    def raw_file_names(self):
        return 'FAUST_remeshed.zip'

    @property
    def processed_file_names(self):
        return ['training.pt', 'test.pt']

    def download(self):
        raise RuntimeError(
            'Dataset not found. Please download {} from {} and move it to {}'.
            format(self.raw_file_names, self.url, self.raw_dir))

    def process(self):
        extract_zip(self.raw_paths[0], self.raw_dir, log=False)

        path = osp.join(self.raw_dir, 'shapes')
        path = osp.join(path, 'tr_reg_{0:03d}.ply')
        faust_diameter = osp.join(self.raw_dir, 'diameters.pt')
        data_list = []
        file_idx = 0
        for i in progressbar.progressbar(range(100)):
            data = read_ply(path.format(i))
            data.diameter = torch.load(faust_diameter)[i]
            if self.pre_filter is not None and not self.pre_filter(data):
                continue
            if self.pre_transform is not None:
                data = self.pre_transform(data)
            del(data.diameter)
            data_list.append(data)
            if i == 79 or i == 99:
                torch.save(self.collate(data_list), self.processed_paths[file_idx])
                data_list = []
                file_idx += 1

        shutil.rmtree(osp.join(self.raw_dir, 'shapes'))