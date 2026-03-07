package com.armenian.flashcards.ui

import android.os.Bundle
import android.view.View
import androidx.activity.viewModels
import androidx.appcompat.app.AppCompatActivity
import androidx.recyclerview.widget.LinearLayoutManager
import com.armenian.flashcards.databinding.ActivityCardListBinding
import com.armenian.flashcards.ui.adapter.FlashcardAdapter
import com.armenian.flashcards.ui.viewmodel.FlashcardViewModel
import com.google.android.material.snackbar.Snackbar

/**
 * Activity to display all flashcards in a list.
 */
class CardListActivity : AppCompatActivity() {
    
    private lateinit var binding: ActivityCardListBinding
    private val viewModel: FlashcardViewModel by viewModels()
    private lateinit var adapter: FlashcardAdapter
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityCardListBinding.inflate(layoutInflater)
        setContentView(binding.root)
        
        setSupportActionBar(binding.toolbar)
        supportActionBar?.setDisplayHomeAsUpEnabled(true)
        
        setupRecyclerView()
        setupObservers()
        setupClickListeners()
    }
    
    private fun setupRecyclerView() {
        adapter = FlashcardAdapter()
        binding.cardsRecyclerView.layoutManager = LinearLayoutManager(this)
        binding.cardsRecyclerView.adapter = adapter
    }
    
    private fun setupObservers() {
        viewModel.getAllFlashcards().observe(this) { cards ->
            if (cards.isEmpty()) {
                binding.emptyStateLayout.visibility = View.VISIBLE
                binding.cardsRecyclerView.visibility = View.GONE
            } else {
                binding.emptyStateLayout.visibility = View.GONE
                binding.cardsRecyclerView.visibility = View.VISIBLE
                adapter.submitList(cards)
            }
        }
    }
    
    private fun setupClickListeners() {
        binding.addCardFab.setOnClickListener {
            Snackbar.make(
                binding.root,
                "Add card feature coming soon!",
                Snackbar.LENGTH_SHORT
            ).show()
        }
    }
    
    override fun onSupportNavigateUp(): Boolean {
        onBackPressed()
        return true
    }
}
