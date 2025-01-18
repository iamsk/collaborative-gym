# Datasets Used in Co-Gym (Simulated)
The core concept of Co-Gym (Simulated) is to create a **sandbox environment** where human-agent collaboration can be studied in a simulated condition without impacting real-world environments or requiring real human participants.

Each task in Co-Gym (Simulated) is associated with a set of pre-collected instances that define concrete shared goals for the human-agent team. Each task instance also includes additional information visible to the simulated user only to create information asymmetry to better study human-agent collaboration dynamics.

## Travel Planning
We leverage the medium and hard cases from the validation set of the [TravelPlanner benchmark](https://github.com/OSU-NLP-Group/TravelPlanner) (102 cases in total) and use its database records to simulate search actions. Hard constraints for each task instance (e.g., budget limits, special accommodation requests) are set as hidden information only visible to the simulated user.

To use the database records, download the [database](https://drive.google.com/file/d/1pF1Sw6pBmq2sFkJvm-LzJOqrmfWoQgxE/view?usp=drive_link) and unzip it to `datasets/TravelPlanner/` folder.

If you run this part of experiments in your paper, please consider also citing the TravelPlanner paper:
```
@inproceedings{xie2024travelplanner,
  title={TravelPlanner: A Benchmark for Real-World Planning with Language Agents},
  author={Xie, Jian and Zhang, Kai and Chen, Jiangjie and Zhu, Tinghui and Lou, Renze and Tian, Yuandong and Xiao, Yanghua and Su, Yu},
  booktitle={Forty-first International Conference on Machine Learning},
  year={2024}
}
```

## Related Work
We leverage the Computer Science (CS) category of the arXiv repository by selecting high-quality conference papers in various areas to construct initial queries (100 cases in total). For each query, the hidden information for simulated humans is curated by extracting 3-9 hints such as
required subheadings, citations, subsection counts, and writing style characteristics.

For SearchPaper in Co-Gym
(Simulated), we index papers from the arXiv CS category
published prior to October 2024 using the `voyage-3` text embedding model and retrieve top 10 papers for each search query. Please refer to [`documentation/indexing`](documentation/indexing) on how to set up the arXiv retriever locally.

This is a newly curated dataset associated with [our paper](https://arxiv.org/abs/2412.15701). Please contact [Vinay Samuel](mailto:vsamuel@andrew.cmu.edu) if you have any question about it.


## Tabular Analysis
We use [DiscoveryBench](https://github.com/allenai/discoverybench), a dataset designed for systems to derive hypotheses based on queries and provided tables. We focus on instances from DiscoveryBench-Real that include unprocessed
table or more than one table, which are considered challenging cases within the original benchmark (110 cases in total). The domain knowledge and dataset metadata fields in the original dataset are treated as additional information available to the simulated human.

If you run this part of experiments in your paper, please consider also citing the DiscoveryBench paper:
```
@article{majumder2024discoverybench,
  author    = "Bodhisattwa Prasad Majumder, Harshit Surana, Dhruv Agarwal, Bhavana Dalvi Mishra, Abhijeetsingh Meena, Aryan Prakhar, Tirth Vora, Tushar Khot, Ashish Sabharwal, Peter Clark",
  title     = "DiscoveryBench: Towards Data-Driven Discovery with Large Language Models",
  journal   = "arXiv",
  year      = "2024",
}
```
