#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import math, typing, copy, time
import torch, torchtext

# REF [site] >> https://pytorch.org/tutorials/beginner/transformer_tutorial.html
class PositionalEncoding(torch.nn.Module):
	def __init__(self, d_model: int, dropout: float = 0.1, max_len: int = 5000):
		super().__init__()

		self.dropout = torch.nn.Dropout(p=dropout)

		position = torch.arange(max_len).unsqueeze(1)
		div_term = torch.exp(torch.arange(0, d_model, 2) * (-math.log(10000.0) / d_model))
		pe = torch.zeros(max_len, 1, d_model)
		pe[:, 0, 0::2] = torch.sin(position * div_term)
		pe[:, 0, 1::2] = torch.cos(position * div_term)
		self.register_buffer("pe", pe)

	def forward(self, x: torch.Tensor) -> torch.Tensor:
		"""
		Args:
			x: Tensor, shape [seq_len, batch_size, embedding_dim]
		"""
		x = x + self.pe[:x.size(0)]
		return self.dropout(x)

# REF [site] >> https://pytorch.org/tutorials/beginner/transformer_tutorial.html
class TransformerModel(torch.nn.Module):
	def __init__(self, num_tokens: int, d_model: int, num_heads: int, dim_ff: int, num_layers: int, dropout: float = 0.5):
		super().__init__()

		self.model_type = "Transformer"
		self.d_model = d_model

		self.encoder = torch.nn.Embedding(num_tokens, d_model)
		self.pos_encoder = PositionalEncoding(d_model, dropout)
		encoder_layer = torch.nn.TransformerEncoderLayer(d_model, nhead=num_heads, dim_feedforward=dim_ff, dropout=dropout, activation=torch.nn.functional.relu, layer_norm_eps=1e-05, batch_first=False, norm_first=False, device=None, dtype=None)
		self.transformer_encoder = torch.nn.TransformerEncoder(encoder_layer, num_layers=num_layers, norm=None, enable_nested_tensor=True)
		self.decoder = torch.nn.Linear(d_model, num_tokens)

		self.init_weights()

	def init_weights(self) -> None:
		initrange = 0.1
		self.encoder.weight.data.uniform_(-initrange, initrange)
		self.decoder.bias.data.zero_()
		self.decoder.weight.data.uniform_(-initrange, initrange)

	def forward(self, src: torch.Tensor, src_mask: torch.Tensor) -> torch.Tensor:
		"""
		Args:
			src: Tensor, shape [seq_len, batch_size]
			src_mask: Tensor, shape [seq_len, seq_len]

		Returns:
			output Tensor of shape [seq_len, batch_size, num_tokens]
		"""
		src = self.encoder(src) * math.sqrt(self.d_model)
		src = self.pos_encoder(src)
		output = self.transformer_encoder(src, src_mask)
		output = self.decoder(output)
		#output = torch.nn.functional.sigmoid(output)
		#output = torch.nn.functional.logsigmoid(output)
		return output

# REF [class] >> TransformerDecoderLayer class in https://github.com/pytorch/pytorch/blob/master/torch/nn/modules/transformer.py.
class DecoderOnlyTransformerLayer(torch.nn.Module):
	__constants__ = ['batch_first', 'norm_first']

	def __init__(self, d_model: int, nhead: int, dim_feedforward: int = 2048, dropout: float = 0.1,
				activation: typing.Union[str, typing.Callable[[torch.Tensor], torch.Tensor]] = torch.nn.functional.relu,
				layer_norm_eps: float = 1e-5, batch_first: bool = False, norm_first: bool = False,
				device=None, dtype=None) -> None:
		factory_kwargs = {'device': device, 'dtype': dtype}
		super(DecoderOnlyTransformerLayer, self).__init__()
		self.self_attn = torch.nn.MultiheadAttention(d_model, nhead, dropout=dropout, batch_first=batch_first, **factory_kwargs)
		#self.multihead_attn = torch.nn.MultiheadAttention(d_model, nhead, dropout=dropout, batch_first=batch_first, **factory_kwargs)
		# Implementation of Feedforward model.
		self.linear1 = torch.nn.Linear(d_model, dim_feedforward, **factory_kwargs)
		self.dropout = torch.nn.Dropout(dropout)
		self.linear2 = torch.nn.Linear(dim_feedforward, d_model, **factory_kwargs)

		self.norm_first = norm_first
		self.norm1 = torch.nn.LayerNorm(d_model, eps=layer_norm_eps, **factory_kwargs)
		#self.norm2 = torch.nn.LayerNorm(d_model, eps=layer_norm_eps, **factory_kwargs)
		self.norm3 = torch.nn.LayerNorm(d_model, eps=layer_norm_eps, **factory_kwargs)
		self.dropout1 = torch.nn.Dropout(dropout)
		#self.dropout2 = torch.nn.Dropout(dropout)
		self.dropout3 = torch.nn.Dropout(dropout)

		# Legacy string support for activation function.
		if isinstance(activation, str):
			self.activation = self._get_activation_fn(activation)
		else:
			self.activation = activation

	def __setstate__(self, state):
		if 'activation' not in state:
			state['activation'] = torch.nn.functional.relu
		super(DecoderOnlyTransformerLayer, self).__setstate__(state)

	#def forward(self, tgt: torch.Tensor, memory: torch.Tensor, tgt_mask: typing.Optional[torch.Tensor] = None, memory_mask: typing.Optional[torch.Tensor] = None,
	#			tgt_key_padding_mask: typing.Optional[torch.Tensor] = None, memory_key_padding_mask: typing.Optional[torch.Tensor] = None) -> torch.Tensor:
	def forward(self, tgt: torch.Tensor, tgt_mask: typing.Optional[torch.Tensor] = None,
				tgt_key_padding_mask: typing.Optional[torch.Tensor] = None) -> torch.Tensor:
		# See Fig. 1 of https://arxiv.org/pdf/2002.04745v1.pdf

		x = tgt
		if self.norm_first:
			x = x + self._sa_block(self.norm1(x), tgt_mask, tgt_key_padding_mask)
			#x = x + self._mha_block(self.norm2(x), memory, memory_mask, memory_key_padding_mask)
			x = x + self._ff_block(self.norm3(x))
		else:
			x = self.norm1(x + self._sa_block(x, tgt_mask, tgt_key_padding_mask))
			#x = self.norm2(x + self._mha_block(x, memory, memory_mask, memory_key_padding_mask))
			x = self.norm3(x + self._ff_block(x))

		return x

	# Self-attention block.
	def _sa_block(self, x: torch.Tensor,
				attn_mask: typing.Optional[torch.Tensor], key_padding_mask: typing.Optional[torch.Tensor]) -> torch.Tensor:
		x = self.self_attn(x, x, x,
						attn_mask=attn_mask,
						key_padding_mask=key_padding_mask,
						need_weights=False)[0]
		return self.dropout1(x)

	# Multihead attention block.
	"""
	def _mha_block(self, x: torch.Tensor, mem: torch.Tensor,
				attn_mask: typing.Optional[torch.Tensor], key_padding_mask: typing.Optional[torch.Tensor]) -> torch.Tensor:
		x = self.multihead_attn(x, mem, mem,
								attn_mask=attn_mask,
								key_padding_mask=key_padding_mask,
								need_weights=False)[0]
		return self.dropout2(x)
	"""

	# Feed-forward block.
	def _ff_block(self, x: torch.Tensor) -> torch.Tensor:
		x = self.linear2(self.dropout(self.activation(self.linear1(x))))
		return self.dropout3(x)

	@staticmethod
	def _get_activation_fn(activation: str) -> typing.Callable[[torch.Tensor], torch.Tensor]:
		if activation == "relu":
			return torch.nn.functional.relu
		elif activation == "gelu":
			return torch.nn.functional.gelu

		raise RuntimeError("activation should be relu/gelu, not {}".format(activation))

# REF [class] >> TransformerDecoder class in https://github.com/pytorch/pytorch/blob/master/torch/nn/modules/transformer.py.
class DecoderOnlyTransformerDecoder(torch.nn.Module):
	__constants__ = ['norm']

	def __init__(self, decoder_layer, num_layers, norm=None):
		super(DecoderOnlyTransformerDecoder, self).__init__()
		self.layers = self._get_clones(decoder_layer, num_layers)
		self.num_layers = num_layers
		self.norm = norm

	#def forward(self, tgt: torch.Tensor, memory: torch.Tensor, tgt_mask: typing.Optional[torch.Tensor] = None,
	#			memory_mask: typing.Optional[torch.Tensor] = None, tgt_key_padding_mask: typing.Optional[torch.Tensor] = None,
	#			memory_key_padding_mask: typing.Optional[torch.Tensor] = None) -> torch.Tensor:
	def forward(self, tgt: torch.Tensor, tgt_mask: typing.Optional[torch.Tensor] = None,
				tgt_key_padding_mask: typing.Optional[torch.Tensor] = None) -> torch.Tensor:
		output = tgt

		for mod in self.layers:
			"""
			output = mod(output, memory, tgt_mask=tgt_mask,
						memory_mask=memory_mask,
						tgt_key_padding_mask=tgt_key_padding_mask,
						memory_key_padding_mask=memory_key_padding_mask)
			"""
			output = mod(output, tgt_mask=tgt_mask, tgt_key_padding_mask=tgt_key_padding_mask)

		if self.norm is not None:
			output = self.norm(output)

		return output

	@staticmethod
	def _get_clones(module, N):
		return torch.nn.ModuleList([copy.deepcopy(module) for i in range(N)])

# REF [paper] >> "Improving Language Understanding by Generative Pre-Training", 2018 (GPT).
class DecoderOnlyTransformerModel(torch.nn.Module):
	def __init__(self, num_tokens: int, d_model: int, num_heads: int, dim_ff: int, num_layers: int, dropout: float = 0.5):
		super().__init__()

		self.model_type = "Transformer"
		self.d_model = d_model

		self.encoder = torch.nn.Embedding(num_tokens, d_model)
		self.pos_encoder = PositionalEncoding(d_model, dropout)
		if False:
			#decoder_layer = torch.nn.TransformerDecoderLayer(d_model, nhead=num_heads, dim_feedforward=dim_ff, dropout=dropout, activation=torch.nn.functional.relu, layer_norm_eps=1e-05, batch_first=False, norm_first=False, device=None, dtype=None)
			#self.transformer_decoder = torch.nn.TransformerDecoder(decoder_layer, num_layers=num_layers, norm=None)
			decoder_layer = DecoderOnlyTransformerLayer(d_model, nhead=num_heads, dim_feedforward=dim_ff, dropout=dropout, activation=torch.nn.functional.relu, layer_norm_eps=1e-05, batch_first=False, norm_first=False, device=None, dtype=None)
			self.transformer_decoder = DecoderOnlyTransformerDecoder(decoder_layer, num_layers=num_layers, norm=None)
		else:
			encoder_layer = torch.nn.TransformerEncoderLayer(d_model, num_heads, dim_feedforward=dim_ff, dropout=dropout, activation=torch.nn.functional.relu, layer_norm_eps=1e-05, batch_first=False, norm_first=False, device=None, dtype=None)
			self.transformer_decoder = torch.nn.TransformerEncoder(encoder_layer, num_layers=num_layers, norm=None, enable_nested_tensor=True)
		self.decoder = torch.nn.Linear(d_model, num_tokens)

		self.init_weights()

	def init_weights(self) -> None:
		initrange = 0.1
		self.encoder.weight.data.uniform_(-initrange, initrange)
		self.decoder.bias.data.zero_()
		self.decoder.weight.data.uniform_(-initrange, initrange)

	def forward(self, src: torch.Tensor, src_mask: torch.Tensor) -> torch.Tensor:
		src = self.encoder(src) * math.sqrt(self.d_model)
		src = self.pos_encoder(src)
		output = self.transformer_decoder(src, src_mask)
		output = self.decoder(output)
		#output = torch.nn.functional.sigmoid(output)
		#output = torch.nn.functional.logsigmoid(output)
		return output

class StandardTransformerModel(torch.nn.Module):
	def __init__(self, num_tokens: int, d_model: int, num_heads: int, dim_ff: int, num_encoder_layers: int, num_decoder_layers: int, dropout: float = 0.5):
		super().__init__()

		self.model_type = "Transformer"
		self.d_model = d_model

		self.src_encoder = torch.nn.Embedding(num_tokens, d_model)
		self.tgt_encoder = torch.nn.Embedding(num_tokens, d_model)
		self.pos_encoder = PositionalEncoding(d_model, dropout)
		"""
		encoder_layer = torch.nn.TransformerEncoderLayer(d_model, nhead=num_heads, dim_feedforward=dim_ff, dropout=dropout, activation=torch.nn.functional.relu, layer_norm_eps=1e-05, batch_first=False, norm_first=False, device=None, dtype=None)
		transformer_encoder = torch.nn.TransformerEncoder(encoder_layer, num_layers=num_encoder_layers, norm=None, enable_nested_tensor=True)
		decoder_layer = torch.nn.TransformerDecoderLayer(d_model, nhead=num_heads, dim_feedforward=dim_ff, dropout=dropout, activation=torch.nn.functional.relu, layer_norm_eps=1e-05, batch_first=False, norm_first=False, device=None, dtype=None)
		transformer_decoder = torch.nn.TransformerDecoder(decoder_layer, num_layers=num_decoder_layers, norm=None)
		self.transformer = ...
		"""
		self.transformer = torch.nn.Transformer(d_model, nhead=num_heads, num_encoder_layers=num_encoder_layers, num_decoder_layers=num_decoder_layers, dim_feedforward=dim_ff, dropout=dropout, activation=torch.nn.functional.relu, custom_encoder=None, custom_decoder=None, layer_norm_eps=1e-05, batch_first=False, norm_first=False, device=None, dtype=None)
		self.decoder = torch.nn.Linear(d_model, num_tokens)

		self.init_weights()

	def init_weights(self) -> None:
		initrange = 0.1
		self.src_encoder.weight.data.uniform_(-initrange, initrange)
		self.tgt_encoder.weight.data.uniform_(-initrange, initrange)
		self.decoder.bias.data.zero_()
		self.decoder.weight.data.uniform_(-initrange, initrange)

	def forward(self, src: torch.Tensor, tgt: torch.Tensor, src_mask: torch.Tensor, tgt_mask: torch.Tensor) -> torch.Tensor:
		"""
		Args:
			src: Tensor, shape [seq_len, batch_size]
			src_mask: Tensor, shape [seq_len, seq_len]

		Returns:
			output Tensor of shape [seq_len, batch_size, num_tokens]
		"""
		src = self.src_encoder(src) * math.sqrt(self.d_model)
		src = self.pos_encoder(src)
		tgt = self.tgt_encoder(tgt) * math.sqrt(self.d_model)
		tgt = self.pos_encoder(tgt)
		output = self.transformer(src, tgt, src_mask, tgt_mask, memory_mask=None, src_key_padding_mask=None, tgt_key_padding_mask=None, memory_key_padding_mask=None)
		output = self.decoder(output)
		#output = torch.nn.functional.sigmoid(output)
		#output = torch.nn.functional.logsigmoid(output)
		return output

# REF [site] >> https://pytorch.org/tutorials/beginner/transformer_tutorial.html
def transformer_tutorial():
	# Load and batch data.
	train_iter = torchtext.datasets.WikiText2(split="train")
	tokenizer = torchtext.data.utils.get_tokenizer("basic_english")
	vocab = torchtext.vocab.build_vocab_from_iterator(map(tokenizer, train_iter), specials=["<unk>"])
	vocab.set_default_index(vocab["<unk>"])

	def data_process(raw_text_iter: torch.utils.data.IterableDataset) -> torch.Tensor:
		"""Converts raw text into a flat Tensor."""
		data = [torch.tensor(vocab(tokenizer(item)), dtype=torch.long) for item in raw_text_iter]
		return torch.cat(tuple(filter(lambda t: t.numel() > 0, data)))

	# Train_iter was "consumed" by the process of building the vocab, so we have to create it again.
	train_iter, val_iter, test_iter = torchtext.datasets.WikiText2()
	train_data = data_process(train_iter)
	val_data = data_process(val_iter)
	test_data = data_process(test_iter)

	device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

	def batchify(data: torch.Tensor, bsz: int) -> torch.Tensor:
		"""Divides the data into bsz separate sequences, removing extra elements that wouldn't cleanly fit.

		Args:
			data: Tensor, shape [N]
			bsz: int, batch size

		Returns:
			Tensor of shape [N // bsz, bsz]
		"""
		seq_len = data.size(0) // bsz
		data = data[:seq_len * bsz]
		data = data.view(bsz, seq_len).t().contiguous()
		return data.to(device)

	batch_size = 20
	eval_batch_size = 10
	train_data = batchify(train_data, batch_size)  # Shape [seq_len, batch_size].
	val_data = batchify(val_data, eval_batch_size)
	test_data = batchify(test_data, eval_batch_size)

	# Functions to generate input and target sequence.
	bptt = 35
	def get_batch(source: torch.Tensor, i: int) -> typing.Tuple[torch.Tensor, torch.Tensor]:
		"""
		Args:
			source: Tensor, shape [full_seq_len, batch_size]
			i: int

		Returns:
			tuple (data, target), where data has shape [seq_len, batch_size] and target has shape [seq_len * batch_size]
		"""
		seq_len = min(bptt, len(source) - 1 - i)
		data = source[i:i+seq_len]
		target = source[i+1:i+1+seq_len]
		return data, target

	# Initiate an instance.
	num_tokens = len(vocab)  # Size of vocabulary.
	dim_model = 200  # Embedding dimension.
	dim_ff = 200  # Dimension of the feedforward network model in torch.nn.TransformerEncoder.
	num_layers = 2  # Number of torch.nn.TransformerEncoderLayer in torch.nn.TransformerEncoder.
	num_heads = 2  # Number of heads in torch.nn.MultiheadAttention.
	dropout = 0.2  # Dropout probability.
	model = TransformerModel(num_tokens, dim_model, num_heads, dim_ff, num_layers, dropout).to(device)

	#-----
	# Run the model.
	criterion = torch.nn.CrossEntropyLoss()
	lr = 5.0  # Learning rate.
	optimizer = torch.optim.SGD(model.parameters(), lr=lr)
	scheduler = torch.optim.lr_scheduler.StepLR(optimizer, 1.0, gamma=0.95)

	# attn_mask:
	#	2D mask: (L, S), where L is the target sequence length, S is the source sequence length.
	#	3D mask: (N * num_heads, L, S), where N is the batch size, L is the target sequence length, S is the source sequence length.
	#	attn_mask ensures that position i is allowed to attend the unmasked positions.
	#	If a ByteTensor is provided, the non-zero positions are not allowed to attend while the zero positions will be unchanged.
	#	If a BoolTensor is provided, positions with "True" are not allowed to attend while "False" values will be unchanged.
	#	If a FloatTensor is provided, it will be added to the attention weight.
	# A square attention mask is required because the self-attention layers in nn.TransformerEncoder are only allowed to attend the earlier positions in the sequence.
	def generate_square_subsequent_mask(sz: int) -> torch.Tensor:
		"""Generates an upper-triangular matrix of -inf, with zeros on diag."""
		return torch.triu(torch.ones(sz, sz) * float("-inf"), diagonal=1)

	def train(model: torch.nn.Module, is_decoder_only: bool = True) -> None:
		model.train()  # Turn on train mode.
		total_loss = 0.
		log_interval = 200
		start_time = time.time()
		if is_decoder_only:
			# Decoder-only transformer model (transformer model architecture in a decoder-only setup).
			src_mask = generate_square_subsequent_mask(bptt).to(device)
		else:
			# Encoder-only transformer model (transformer model architecture in an encoder-only setup).
			src_mask = None
			#src_mask = torch.zeros(bptt, bptt).to(device)

		num_batches = len(train_data) // bptt
		for batch, i in enumerate(range(0, train_data.size(0) - 1, bptt)):
			data, targets = get_batch(train_data, i)
			seq_len = data.size(0)
			if src_mask is not None and seq_len != bptt:  # Only on last batch.
				src_mask = src_mask[:seq_len, :seq_len]
			output = model(data, src_mask)
			loss = criterion(output.view(-1, num_tokens), targets.reshape(-1))

			optimizer.zero_grad()
			loss.backward()
			torch.nn.utils.clip_grad_norm_(model.parameters(), 0.5)
			optimizer.step()

			total_loss += loss.item()
			if batch % log_interval == 0 and batch > 0:
				lr = scheduler.get_last_lr()[0]
				ms_per_batch = (time.time() - start_time) * 1000 / log_interval
				cur_loss = total_loss / log_interval
				ppl = math.exp(cur_loss)
				print(f"| epoch {epoch:3d} | {batch:5d}/{num_batches:5d} batches | "
					f"lr {lr:02.2f} | ms/batch {ms_per_batch:5.2f} | "
					f"loss {cur_loss:5.2f} | ppl {ppl:8.2f}")
				total_loss = 0
				start_time = time.time()

	def evaluate(model: torch.nn.Module, eval_data: torch.Tensor, is_decoder_only: bool = True) -> float:
		model.eval()  # Turn on evaluation mode.
		total_loss = 0.0
		if is_decoder_only:
			# Decoder-only transformer model (transformer model architecture in a decoder-only setup).
			src_mask = generate_square_subsequent_mask(bptt).to(device)
		else:
			# Encoder-only transformer model (transformer model architecture in an encoder-only setup).
			src_mask = None
			#src_mask = torch.zeros(bptt, bptt).to(device)
		with torch.no_grad():
			for i in range(0, eval_data.size(0) - 1, bptt):
				data, targets = get_batch(eval_data, i)
				seq_len = data.size(0)
				if src_mask is not None and seq_len != bptt:
					src_mask = src_mask[:seq_len, :seq_len]
				output = model(data, src_mask)
				total_loss += seq_len * criterion(output.view(-1, num_tokens), targets.reshape(-1)).item()
		return total_loss / (len(eval_data) - 1)

	# Loop over epochs.
	# Save the model if the validation loss is the best we've seen so far. Adjust the learning rate after each epoch.
	best_val_loss = float("inf")
	epochs = 3
	best_model = None
	is_decoder_only = True

	for epoch in range(1, epochs + 1):
		epoch_start_time = time.time()
		train(model, is_decoder_only)
		val_loss = evaluate(model, val_data, is_decoder_only)
		val_ppl = math.exp(val_loss)
		elapsed = time.time() - epoch_start_time
		print("-" * 89)
		print(f"| end of epoch {epoch:3d} | time: {elapsed:5.2f}s | valid loss {val_loss:5.2f} | valid ppl {val_ppl:8.2f}")
		print("-" * 89)

		if val_loss < best_val_loss:
			best_val_loss = val_loss
			best_model = copy.deepcopy(model)

		scheduler.step()

	#-----
	# Evaluate the best model on the test dataset.
	test_loss = evaluate(best_model, test_data)
	test_ppl = math.exp(test_loss)
	print("=" * 89)
	print(f"| End of training | test loss {test_loss:5.2f} | test ppl {test_ppl:8.2f}")
	print("=" * 89)

def decoder_based_transformer_test():
	# Load and batch data.
	train_iter = torchtext.datasets.WikiText2(split="train")
	tokenizer = torchtext.data.utils.get_tokenizer("basic_english")
	vocab = torchtext.vocab.build_vocab_from_iterator(map(tokenizer, train_iter), specials=["<unk>"])
	vocab.set_default_index(vocab["<unk>"])

	def data_process(raw_text_iter: torch.utils.data.IterableDataset) -> torch.Tensor:
		"""Converts raw text into a flat Tensor."""
		data = [torch.tensor(vocab(tokenizer(item)), dtype=torch.long) for item in raw_text_iter]
		return torch.cat(tuple(filter(lambda t: t.numel() > 0, data)))

	# Train_iter was "consumed" by the process of building the vocab, so we have to create it again.
	train_iter, val_iter, test_iter = torchtext.datasets.WikiText2()
	train_data = data_process(train_iter)
	val_data = data_process(val_iter)
	test_data = data_process(test_iter)

	device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

	def batchify(data: torch.Tensor, bsz: int) -> torch.Tensor:
		"""Divides the data into bsz separate sequences, removing extra elements that wouldn't cleanly fit.

		Args:
			data: Tensor, shape [N]
			bsz: int, batch size

		Returns:
			Tensor of shape [N // bsz, bsz]
		"""
		seq_len = data.size(0) // bsz
		data = data[:seq_len * bsz]
		data = data.view(bsz, seq_len).t().contiguous()
		return data.to(device)

	batch_size = 20
	eval_batch_size = 10
	train_data = batchify(train_data, batch_size)  # Shape [seq_len, batch_size].
	val_data = batchify(val_data, eval_batch_size)
	test_data = batchify(test_data, eval_batch_size)

	# Functions to generate input and target sequence.
	bptt = 35
	def get_batch(source: torch.Tensor, i: int) -> typing.Tuple[torch.Tensor, torch.Tensor]:
		"""
		Args:
			source: Tensor, shape [full_seq_len, batch_size]
			i: int

		Returns:
			tuple (data, target), where data has shape [seq_len, batch_size] and target has shape [seq_len * batch_size]
		"""
		seq_len = min(bptt, len(source) - 1 - i)
		data = source[i:i+seq_len]
		target = source[i+1:i+1+seq_len]
		return data, target

	# Initiate an instance.
	num_tokens = len(vocab)  # Size of vocabulary.
	dim_model = 200  # Embedding dimension.
	dim_ff = 200  # Dimension of the feedforward network model in torch.nn.TransformerDecoder.
	num_layers = 2  # Number of torch.nn.TransformerDecoderLayer in torch.nn.TransformerDecoder.
	num_heads = 2  # Number of heads in torch.nn.MultiheadAttention.
	dropout = 0.2  # Dropout probability.
	model = DecoderOnlyTransformerModel(num_tokens, dim_model, num_heads, dim_ff, num_layers, dropout).to(device)

	#-----
	# Run the model.
	criterion = torch.nn.CrossEntropyLoss()
	lr = 5.0  # Learning rate.
	optimizer = torch.optim.SGD(model.parameters(), lr=lr)
	scheduler = torch.optim.lr_scheduler.StepLR(optimizer, 1.0, gamma=0.95)

	# attn_mask:
	#	2D mask: (L, S), where L is the target sequence length, S is the source sequence length.
	#	3D mask: (N * num_heads, L, S), where N is the batch size, L is the target sequence length, S is the source sequence length.
	#	attn_mask ensures that position i is allowed to attend the unmasked positions.
	#	If a ByteTensor is provided, the non-zero positions are not allowed to attend while the zero positions will be unchanged.
	#	If a BoolTensor is provided, positions with "True" are not allowed to attend while "False" values will be unchanged.
	#	If a FloatTensor is provided, it will be added to the attention weight.
	# A square attention mask is required because the self-attention layers in nn.TransformerEncoder are only allowed to attend the earlier positions in the sequence.
	def generate_square_subsequent_mask(sz: int) -> torch.Tensor:
		"""Generates an upper-triangular matrix of -inf, with zeros on diag."""
		return torch.triu(torch.ones(sz, sz) * float("-inf"), diagonal=1)

	def train(model: torch.nn.Module, is_decoder_only: bool = True) -> None:
		model.train()  # Turn on train mode.
		total_loss = 0.
		log_interval = 200
		start_time = time.time()
		if is_decoder_only:
			# Decoder-only transformer model (transformer model architecture in a decoder-only setup).
			src_mask = generate_square_subsequent_mask(bptt).to(device)
		else:
			# Encoder-only transformer model (transformer model architecture in an encoder-only setup).
			src_mask = None
			#src_mask = torch.zeros(bptt, bptt).to(device)

		num_batches = len(train_data) // bptt
		for batch, i in enumerate(range(0, train_data.size(0) - 1, bptt)):
			data, targets = get_batch(train_data, i)
			seq_len = data.size(0)
			if seq_len != bptt:  # Only on last batch.
				src_mask = src_mask[:seq_len, :seq_len]
			output = model(data, src_mask)
			loss = criterion(output.view(-1, num_tokens), targets.reshape(-1))

			optimizer.zero_grad()
			loss.backward()
			torch.nn.utils.clip_grad_norm_(model.parameters(), 0.5)
			optimizer.step()

			total_loss += loss.item()
			if batch % log_interval == 0 and batch > 0:
				lr = scheduler.get_last_lr()[0]
				ms_per_batch = (time.time() - start_time) * 1000 / log_interval
				cur_loss = total_loss / log_interval
				ppl = math.exp(cur_loss)
				print(f"| epoch {epoch:3d} | {batch:5d}/{num_batches:5d} batches | "
					f"lr {lr:02.2f} | ms/batch {ms_per_batch:5.2f} | "
					f"loss {cur_loss:5.2f} | ppl {ppl:8.2f}")
				total_loss = 0
				start_time = time.time()

	def evaluate(model: torch.nn.Module, eval_data: torch.Tensor, is_decoder_only: bool = True) -> float:
		model.eval()  # Turn on evaluation mode.
		total_loss = 0.0
		if is_decoder_only:
			# Decoder-only transformer model (transformer model architecture in a decoder-only setup).
			src_mask = generate_square_subsequent_mask(bptt).to(device)
		else:
			# Encoder-only transformer model (transformer model architecture in an encoder-only setup).
			src_mask = None
			#src_mask = torch.zeros(bptt, bptt).to(device)
		with torch.no_grad():
			for i in range(0, eval_data.size(0) - 1, bptt):
				data, targets = get_batch(eval_data, i)
				seq_len = data.size(0)
				if seq_len != bptt:
					src_mask = src_mask[:seq_len, :seq_len]
				output = model(data, src_mask)
				total_loss += seq_len * criterion(output.view(-1, num_tokens), targets.reshape(-1)).item()
		return total_loss / (len(eval_data) - 1)

	# Loop over epochs.
	# Save the model if the validation loss is the best we've seen so far. Adjust the learning rate after each epoch.
	best_val_loss = float("inf")
	epochs = 3
	best_model = None
	is_decoder_only = True

	for epoch in range(1, epochs + 1):
		epoch_start_time = time.time()
		train(model, is_decoder_only)
		val_loss = evaluate(model, val_data, is_decoder_only)
		val_ppl = math.exp(val_loss)
		elapsed = time.time() - epoch_start_time
		print("-" * 89)
		print(f"| end of epoch {epoch:3d} | time: {elapsed:5.2f}s | valid loss {val_loss:5.2f} | valid ppl {val_ppl:8.2f}")
		print("-" * 89)

		if val_loss < best_val_loss:
			best_val_loss = val_loss
			best_model = copy.deepcopy(model)

		scheduler.step()

	#-----
	# Evaluate the best model on the test dataset.
	test_loss = evaluate(best_model, test_data)
	test_ppl = math.exp(test_loss)
	print("=" * 89)
	print(f"| End of training | test loss {test_loss:5.2f} | test ppl {test_ppl:8.2f}")
	print("=" * 89)

def standard_transformer_test():
	# Load and batch data.
	train_iter = torchtext.datasets.WikiText2(split="train")
	tokenizer = torchtext.data.utils.get_tokenizer("basic_english")
	vocab = torchtext.vocab.build_vocab_from_iterator(map(tokenizer, train_iter), specials=["<unk>"])
	vocab.set_default_index(vocab["<unk>"])

	def data_process(raw_text_iter: torch.utils.data.IterableDataset) -> torch.Tensor:
		"""Converts raw text into a flat Tensor."""
		data = [torch.tensor(vocab(tokenizer(item)), dtype=torch.long) for item in raw_text_iter]
		return torch.cat(tuple(filter(lambda t: t.numel() > 0, data)))

	# Train_iter was "consumed" by the process of building the vocab, so we have to create it again.
	train_iter, val_iter, test_iter = torchtext.datasets.WikiText2()
	train_data = data_process(train_iter)
	val_data = data_process(val_iter)
	test_data = data_process(test_iter)

	device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

	def batchify(data: torch.Tensor, bsz: int) -> torch.Tensor:
		"""Divides the data into bsz separate sequences, removing extra elements that wouldn't cleanly fit.

		Args:
			data: Tensor, shape [N]
			bsz: int, batch size

		Returns:
			Tensor of shape [N // bsz, bsz]
		"""
		seq_len = data.size(0) // bsz
		data = data[:seq_len * bsz]
		data = data.view(bsz, seq_len).t().contiguous()
		return data.to(device)

	batch_size = 20
	eval_batch_size = 10
	train_data = batchify(train_data, batch_size)  # Shape [seq_len, batch_size].
	val_data = batchify(val_data, eval_batch_size)
	test_data = batchify(test_data, eval_batch_size)

	# Functions to generate input and target sequence.
	bptt = 35
	def get_batch(source: torch.Tensor, i: int) -> typing.Tuple[torch.Tensor, torch.Tensor]:
		"""
		Args:
			source: Tensor, shape [full_seq_len, batch_size]
			i: int

		Returns:
			tuple (data, target), where data has shape [seq_len, batch_size] and target has shape [seq_len * batch_size]
		"""
		seq_len = min(bptt, len(source) - 1 - i)
		encoder_input = source[i:i+seq_len]
		# FIXME [fix] >> decoder_input & decoder_output have to be properly assigned.
		decoder_input = source[i+1:i+1+seq_len]
		decoder_output = source[i+1:i+1+seq_len]
		return encoder_input, decoder_input, decoder_output

	# Initiate an instance.
	num_tokens = len(vocab)  # Size of vocabulary.
	dim_model = 200  # Embedding dimension.
	dim_ff = 200  # Dimension of the feedforward network model in torch.nn.TransformerEncoder & torch.nn.TransformerDecoder.
	num_encoder_layers = 2  # Number of torch.nn.TransformerEncoderLayer in torch.nn.TransformerEncoder.
	num_decoder_layers = 2  # Number of torch.nn.TransformerDecoderLayer in torch.nn.TransformerDecoder.
	num_heads = 2  # Number of heads in torch.nn.MultiheadAttention.
	dropout = 0.2  # Dropout probability.
	model = StandardTransformerModel(num_tokens, dim_model, num_heads, dim_ff, num_encoder_layers, num_decoder_layers, dropout).to(device)

	#-----
	# Run the model.
	criterion = torch.nn.CrossEntropyLoss()
	lr = 5.0  # Learning rate.
	optimizer = torch.optim.SGD(model.parameters(), lr=lr)
	scheduler = torch.optim.lr_scheduler.StepLR(optimizer, 1.0, gamma=0.95)

	# attn_mask:
	#	2D mask: (L, S), where L is the target sequence length, S is the source sequence length.
	#	3D mask: (N * num_heads, L, S), where N is the batch size, L is the target sequence length, S is the source sequence length.
	#	attn_mask ensures that position i is allowed to attend the unmasked positions.
	#	If a ByteTensor is provided, the non-zero positions are not allowed to attend while the zero positions will be unchanged.
	#	If a BoolTensor is provided, positions with "True" are not allowed to attend while "False" values will be unchanged.
	#	If a FloatTensor is provided, it will be added to the attention weight.
	# A square attention mask is required because the self-attention layers in nn.TransformerEncoder are only allowed to attend the earlier positions in the sequence.
	def generate_square_subsequent_mask(sz: int) -> torch.Tensor:
		"""Generates an upper-triangular matrix of -inf, with zeros on diag."""
		return torch.triu(torch.ones(sz, sz) * float("-inf"), diagonal=1)

	def train(model: torch.nn.Module) -> None:
		model.train()  # Turn on train mode.
		total_loss = 0.
		log_interval = 200
		start_time = time.time()
		src_mask = None
		#src_mask = torch.zeros(bptt, bptt).to(device)
		tgt_mask = generate_square_subsequent_mask(bptt).to(device)

		num_batches = len(train_data) // bptt
		for batch, i in enumerate(range(0, train_data.size(0) - 1, bptt)):
			encoder_input, decoder_input, decoder_output = get_batch(train_data, i)
			seq_len = encoder_input.size(0)
			if src_mask is not None and seq_len != bptt:  # Only on last batch.
				src_mask = src_mask[:seq_len, :seq_len]
			if tgt_mask is not None and seq_len != bptt:  # Only on last batch.
				tgt_mask = tgt_mask[:seq_len, :seq_len]
			output = model(encoder_input, decoder_input, src_mask, tgt_mask)
			loss = criterion(output.view(-1, num_tokens), decoder_output.reshape(-1))

			optimizer.zero_grad()
			loss.backward()
			torch.nn.utils.clip_grad_norm_(model.parameters(), 0.5)
			optimizer.step()

			total_loss += loss.item()
			if batch % log_interval == 0 and batch > 0:
				lr = scheduler.get_last_lr()[0]
				ms_per_batch = (time.time() - start_time) * 1000 / log_interval
				cur_loss = total_loss / log_interval
				ppl = math.exp(cur_loss)
				print(f"| epoch {epoch:3d} | {batch:5d}/{num_batches:5d} batches | "
					f"lr {lr:02.2f} | ms/batch {ms_per_batch:5.2f} | "
					f"loss {cur_loss:5.2f} | ppl {ppl:8.2f}")
				total_loss = 0
				start_time = time.time()

	def evaluate(model: torch.nn.Module, eval_data: torch.Tensor) -> float:
		model.eval()  # Turn on evaluation mode.
		total_loss = 0.0
		src_mask = None
		#src_mask = torch.zeros(bptt, bptt).to(device)
		tgt_mask = generate_square_subsequent_mask(bptt).to(device)
		with torch.no_grad():
			for i in range(0, eval_data.size(0) - 1, bptt):
				encoder_input, decoder_input, decoder_output = get_batch(eval_data, i)
				seq_len = encoder_input.size(0)
				if src_mask is not None and seq_len != bptt:
					src_mask = src_mask[:seq_len, :seq_len]
				if tgt_mask is not None and seq_len != bptt:  # Only on last batch.
					tgt_mask = tgt_mask[:seq_len, :seq_len]
				output = model(encoder_input, decoder_input, src_mask, tgt_mask)
				total_loss += seq_len * criterion(output.view(-1, num_tokens), decoder_output.reshape(-1)).item()
		return total_loss / (len(eval_data) - 1)

	# Loop over epochs.
	# Save the model if the validation loss is the best we've seen so far. Adjust the learning rate after each epoch.
	best_val_loss = float("inf")
	epochs = 3
	best_model = None

	for epoch in range(1, epochs + 1):
		epoch_start_time = time.time()
		train(model)
		val_loss = evaluate(model, val_data)
		val_ppl = math.exp(val_loss)
		elapsed = time.time() - epoch_start_time
		print("-" * 89)
		print(f"| end of epoch {epoch:3d} | time: {elapsed:5.2f}s | valid loss {val_loss:5.2f} | valid ppl {val_ppl:8.2f}")
		print("-" * 89)

		if val_loss < best_val_loss:
			best_val_loss = val_loss
			best_model = copy.deepcopy(model)

		scheduler.step()

	#-----
	# Evaluate the best model on the test dataset.
	test_loss = evaluate(best_model, test_data)
	test_ppl = math.exp(test_loss)
	print("=" * 89)
	print(f"| End of training | test loss {test_loss:5.2f} | test ppl {test_ppl:8.2f}")
	print("=" * 89)

def main():
	# Transformer layers:
	#	torch.nn.Transformer
	#	torch.nn.TransformerEncoder
	#	torch.nn.TransformerDecoder
	#	torch.nn.TransformerEncoderLayer
	#	torch.nn.TransformerDecoderLayer

	# REF [site] >> https://pytorch.org/blog/a-better-transformer-for-fast-transformer-encoder-inference/

	#--------------------
	# Encoder-only or decoder-only transformer model.
	#	Encoder-only transformer model = transformer model architecture in an encoder-only setup.
	#	Decoder-only transformer model = transformer model architecture in a decoder-only setup.

	# NOTE [info] >> The difference between encoder-only transformer and decoder-only transformer models.
	#	Both models use only the left part of the standard transformer model.
	#	Encoder-only transformer model uses the multi-head self-attention layers.
	#	But decoder-only transformer model uses the "masked" multi-head self-attention layers.

	transformer_tutorial()
	#decoder_based_transformer_test()

	#--------------------
	# Standard transformer model.
	#	Encoder-decoder transformer model = transformer model architecture in an encoder-decoder setup.

	#standard_transformer_test()  # Not yet completed.

#--------------------------------------------------------------------

if "__main__" == __name__:
	main()