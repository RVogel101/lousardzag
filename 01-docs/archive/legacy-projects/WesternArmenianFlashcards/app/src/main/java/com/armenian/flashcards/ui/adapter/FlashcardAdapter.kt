package com.armenian.flashcards.ui.adapter

import android.view.LayoutInflater
import android.view.ViewGroup
import androidx.recyclerview.widget.DiffUtil
import androidx.recyclerview.widget.ListAdapter
import androidx.recyclerview.widget.RecyclerView
import com.armenian.flashcards.data.model.Flashcard
import com.armenian.flashcards.databinding.ItemFlashcardBinding
import java.text.SimpleDateFormat
import java.util.*

/**
 * Adapter for displaying flashcards in a RecyclerView.
 */
class FlashcardAdapter : ListAdapter<Flashcard, FlashcardAdapter.FlashcardViewHolder>(FlashcardDiffCallback()) {
    
    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): FlashcardViewHolder {
        val binding = ItemFlashcardBinding.inflate(
            LayoutInflater.from(parent.context),
            parent,
            false
        )
        return FlashcardViewHolder(binding)
    }
    
    override fun onBindViewHolder(holder: FlashcardViewHolder, position: Int) {
        holder.bind(getItem(position))
    }
    
    class FlashcardViewHolder(
        private val binding: ItemFlashcardBinding
    ) : RecyclerView.ViewHolder(binding.root) {
        
        fun bind(flashcard: Flashcard) {
            binding.frontTextView.text = flashcard.frontText
            binding.backTextView.text = flashcard.backText
            binding.intervalTextView.text = "Interval: ${flashcard.interval}d"
            binding.reviewsTextView.text = "Reviews: ${flashcard.totalReviews}"
        }
    }
    
    class FlashcardDiffCallback : DiffUtil.ItemCallback<Flashcard>() {
        override fun areItemsTheSame(oldItem: Flashcard, newItem: Flashcard): Boolean {
            return oldItem.id == newItem.id
        }
        
        override fun areContentsTheSame(oldItem: Flashcard, newItem: Flashcard): Boolean {
            return oldItem == newItem
        }
    }
}
